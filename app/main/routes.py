# app/main/routes.py
import os
import uuid
from flask import render_template, redirect, url_for, request, flash, current_app
from app.extensions import db
from app.models import Feedback, News, Organization
from app.utils import get_current_user_obj, permission_required_manual, log_user_activity, check_user_permission
from . import main_bp
from sqlalchemy import func
from werkzeug.utils import secure_filename

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/university', methods=['GET', 'POST'])
def university():
    """Страница 'Об университете' с возможностью загрузки PDF-документов для админов"""
    upload_path = os.path.join(current_app.static_folder, 'uploads', 'university')
    
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    if request.method == 'POST' and check_user_permission('manage_organizations'):
        file = request.files.get('doc_file')
        doc_name = request.form.get('doc_name')
        
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(f"{doc_name}_{uuid.uuid4().hex[:8]}.pdf")
            file.save(os.path.join(upload_path, filename))
            log_user_activity(f"Загружен официальный документ: {doc_name}", "UniversityDoc")
            flash(f'Документ "{doc_name}" успешно загружен.', 'success')
            return redirect(url_for('main.university'))
        else:
            flash('Ошибка: допускаются только файлы в формате PDF.', 'danger')

    documents = []
    if os.path.exists(upload_path):
        for filename in sorted(os.listdir(upload_path)):
            if filename.endswith('.pdf'):
                # до первого подчеркивания
                display_name = filename.rsplit('_', 1)[0]
                documents.append({
                    'filename': filename,
                    'name': display_name,
                    'url': url_for('static', filename=f'uploads/university/{filename}')
                })

    return render_template('university.html', documents=documents)

@main_bp.route('/university/delete-doc/<string:filename>', methods=['POST'])
@permission_required_manual('manage_organizations')
def delete_university_doc(filename):
    """Удаление документа университета"""
    file_path = os.path.join(current_app.static_folder, 'uploads', 'university', filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        log_user_activity(f"Удален официальный документ: {filename}", "UniversityDoc")
        flash('Документ удален.', 'info')
    return redirect(url_for('main.university'))

@main_bp.route('/analytics')
def analytics():
    """Страница 'Аналитика'"""
    stats = {
        'total_orgs': Organization.query.count(),
        'by_type': db.session.query(Organization.org_type, func.count(Organization.id)).group_by(Organization.org_type).all(),
        'total_news': News.query.count()
    }
    return render_template('analytics.html', stats=stats)

@main_bp.route('/news')
def news_list():
    page = request.args.get('page', 1, type=int)
    news_items = News.query.order_by(News.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('news_list.html', news_items=news_items)

@main_bp.route('/news/<int:news_id>')
def view_news_item(news_id):
    news_item = News.query.get_or_404(news_id)
    return render_template('news_detail.html', news_item=news_item)

@main_bp.route('/news/add', methods=['GET', 'POST'])
@permission_required_manual('manage_news')
def add_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            flash('Заголовок и содержание не могут быть пустыми.', 'danger')
            return render_template('news_form.html', form_data=request.form)
        
        current_user = get_current_user_obj()
        new_item = News(title=title, content=content, user_id=current_user.id)
        db.session.add(new_item)
        db.session.commit()
        
        log_user_activity(f"Создана новость: '{title}'", "News", new_item.id)
        flash('Новость успешно создана.', 'success')
        return redirect(url_for('main.news_list'))
        
    return render_template('news_form.html', form_data={})

@main_bp.route('/news/edit/<int:news_id>', methods=['GET', 'POST'])
@permission_required_manual('manage_news')
def edit_news(news_id):
    news_item = News.query.get_or_404(news_id)
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            flash('Заголовок и содержание не могут быть пустыми.', 'danger')
            return render_template('news_form.html', news_item=news_item)
        
        news_item.title = title
        news_item.content = content
        db.session.commit()
        
        log_user_activity(f"Отредактирована новость: '{title}'", "News", news_item.id)
        flash('Новость успешно обновлена.', 'success')
        return redirect(url_for('main.view_news_item', news_id=news_item.id))

    return render_template('news_form.html', news_item=news_item)

@main_bp.route('/news/delete/<int:news_id>', methods=['POST'])
@permission_required_manual('manage_news')
def delete_news(news_id):
    news_item = News.query.get_or_404(news_id)
    title = news_item.title
    db.session.delete(news_item)
    db.session.commit()
    
    log_user_activity(f"Удалена новость: '{title}'", "News", news_id)
    flash('Новость успешно удалена.', 'success')
    return redirect(url_for('main.news_list'))

@main_bp.route('/contacts', methods=['GET', 'POST'])
def contacts():
    user = get_current_user_obj()
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not all([name, email, subject, message]):
            flash('Пожалуйста, заполните все поля формы.', 'danger')
            return render_template('contacts.html', form_data=request.form, user=user)
        
        feedback_entry = Feedback(
            name=name,
            email=email,
            subject=subject,
            message=message,
            user_id=user.id if user else None
        )
        db.session.add(feedback_entry)
        db.session.commit()
        
        log_user_activity(f"Отправлено сообщение обратной связи: '{subject}'", "Feedback", feedback_entry.id)
        flash('Спасибо! Ваше сообщение успешно отправлено.', 'success')
        return redirect(url_for('main.contacts'))

    return render_template('contacts.html', user=user, form_data={})

@main_bp.route('/help')
def help_page():
    return render_template('help.html')

@main_bp.route('/feedback')
@permission_required_manual('manage_users') 
def view_feedback():
    page = request.args.get('page', 1, type=int)
    feedback_items = Feedback.query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('feedback_list.html', feedback_items=feedback_items)

@main_bp.route('/feedback/<int:feedback_id>/toggle_read', methods=['POST'])
@permission_required_manual('manage_users')
def toggle_feedback_read(feedback_id):
    feedback_item = Feedback.query.get_or_404(feedback_id)
    feedback_item.is_read = not feedback_item.is_read
    db.session.commit()
    return redirect(url_for('main.view_feedback'))
# app/main/routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.extensions import db
from app.models import Feedback
from app.utils import get_current_user_obj, permission_required_manual, log_user_activity
from . import main_bp

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

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
@permission_required_manual('manage_users') # Только админы могут смотреть
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
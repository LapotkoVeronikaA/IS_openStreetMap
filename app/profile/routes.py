# app/profile/routes.py
from flask import render_template, request, redirect, url_for, flash, current_app
from app.models import User
from app.extensions import db
from app.utils import get_current_user_obj, permission_required_manual, log_user_activity, check_user_permission, login_required_manual
from . import profile_bp

@profile_bp.route('/')
@login_required_manual
def index():
    # Перенаправляем на страницу просмотра профиля по умолчанию
    current_user = get_current_user_obj()
    return redirect(url_for('profile.view', user_id=current_user.id))

@profile_bp.route('/view/<int:user_id>')
@permission_required_manual('view_profile')
def view(user_id):
    user_to_view = User.query.get_or_404(user_id)
    current_user = get_current_user_obj()
    
    # Только админ может смотреть чужие профили
    if user_to_view.id != current_user.id and not check_user_permission('manage_users'):
        flash('У вас нет прав для просмотра этого профиля.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    return render_template('profile_view.html', user=user_to_view)

@profile_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@permission_required_manual('view_profile')
def edit(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    current_user = get_current_user_obj()
    
    # Редактировать может либо сам пользователь, либо админ
    can_edit_all = check_user_permission('manage_users')
    if user_to_edit.id != current_user.id and not can_edit_all:
        flash('У вас нет прав для редактирования этого профиля.', 'danger')
        return redirect(url_for('profile.view', user_id=user_id))
    
    if request.method == 'POST':
        changes = {}
        
        # Обновление полей, которые может менять сам пользователь
        form_fields_to_check = ['full_name', 'department', 'position', 'contact_info']
        for field in form_fields_to_check:
            new_value = request.form.get(field)
            old_value = getattr(user_to_edit, field)
            if (new_value or "") != (old_value or ""):
                changes[field] = {'old': old_value, 'new': new_value}
                setattr(user_to_edit, field, new_value)
        
        # Поля, которые может менять только админ
        if can_edit_all:
            new_username = request.form.get('username')
            if new_username and new_username != user_to_edit.username:
                if User.query.filter(User.id != user_to_edit.id, User.username == new_username).first():
                    flash(f'Имя пользователя {new_username} уже занято.', 'warning')
                    return render_template('profile_edit.html', user=user_to_edit, can_edit_all=can_edit_all)
                changes['username'] = {'old': user_to_edit.username, 'new': new_username}
                user_to_edit.username = new_username

        if not changes:
            flash('Нет изменений для сохранения.', 'info')
            return redirect(url_for('profile.view', user_id=user_id))
            
        try:
            db.session.commit()
            log_user_activity(f"Обновление профиля {user_to_edit.username}", "User", user_id, details_dict=changes)
            flash('Профиль успешно обновлен.', 'success')
            return redirect(url_for('profile.view', user_id=user_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении профиля: {e}', 'danger')
            current_app.logger.error(f"Ошибка обновления профиля {user_id}: {e}")

    return render_template('profile_edit.html', user=user_to_edit, can_edit_all=can_edit_all)
# app/users/routes.py
from flask import render_template, request, redirect, url_for, flash, current_app
from app.models import User, Organization, Group
from app.extensions import db
from app.utils import (
    log_user_activity,
    permission_required_manual
)
from . import users_bp

@users_bp.route('/')
@permission_required_manual('manage_users')
def user_management():
    users = User.query.options(db.joinedload(User.group)).all()
    return render_template('users.html', users=users)

@users_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@permission_required_manual('manage_users')
def edit_user(id):
    user = User.query.options(db.joinedload(User.group)).get_or_404(id)
    all_groups = Group.query.order_by(Group.name).all()

    if request.method == 'POST':
        changes = {}

        new_username = request.form.get('username')
        if new_username != user.username:
            if User.query.filter(User.id != id, User.username == new_username).first():
                flash(f'Имя пользователя {new_username} уже занято.', 'warning')
                return render_template('edit_user.html', user=user, all_groups=all_groups)
            changes['username'] = {'old': user.username, 'new': new_username}
            user.username = new_username
        
        new_password_plain = request.form.get('password')
        if new_password_plain:
            user.password = new_password_plain
            changes['password'] = {'old': '********', 'new': '********'}
        
        form_fields_to_check = ['full_name', 'department', 'position', 'contact_info']
        for field in form_fields_to_check:
            new_value = request.form.get(field)
            old_value = getattr(user, field)
            if (new_value or "") != (old_value or ""):
                changes[field] = {'old': old_value, 'new': new_value}
                setattr(user, field, new_value)
        
        new_group_id = request.form.get('group_id', type=int)
        if new_group_id and new_group_id != user.group_id:
            new_group = db.session.get(Group, new_group_id)
            if new_group:
                changes['group'] = {'old': user.group.name if user.group else 'N/A', 'new': new_group.name}
                user.group_id = new_group_id
            else:
                flash(f'Выбрана несуществующая группа.', 'warning')

        if not changes:
            flash('Нет изменений для сохранения.', 'info')
            return redirect(url_for('users.user_management'))

        try:
            db.session.commit()
            log_user_activity(f"Обновление пользователя {user.username}", "User", user.id, details_dict=changes)
            flash('Пользователь успешно обновлен!', 'success')
            return redirect(url_for('users.user_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении пользователя: {str(e)}', 'danger')
            current_app.logger.error(f"Ошибка обновления пользователя {user.username}: {e}")
            return render_template('edit_user.html', user=user, all_groups=all_groups)

    return render_template('edit_user.html', user=user, all_groups=all_groups)

@users_bp.route('/add', methods=['GET', 'POST'])
@permission_required_manual('manage_users')
def add_user():
    all_groups = Group.query.order_by(Group.name).all()

    if request.method == 'POST':
        username = request.form.get('username')
        if User.query.filter_by(username=username).first():
            flash(f'Пользователь с именем {username} уже существует.', 'warning')
            return render_template('add_user.html', form_data=request.form, all_groups=all_groups)

        new_user = User(
            username=username,
            password=request.form.get('password'),
            group_id=request.form.get('group_id', type=int),
            full_name=request.form.get('full_name'),
            department=request.form.get('department'),
            position=request.form.get('position'),
            contact_info=request.form.get('contact_info')
        )
        
        db.session.add(new_user)
        try:
            db.session.commit()
            
            new_group_name = db.session.get(Group, new_user.group_id).name if new_user.group_id else "N/A"
            user_data_for_log = {
                "username": new_user.username, "group": new_group_name, "full_name": new_user.full_name,
            }
            log_user_activity(f"Создание пользователя {new_user.username}", "User", new_user.id, {"created_data": user_data_for_log})

            flash('Пользователь успешно добавлен!', 'success')
            return redirect(url_for('users.user_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении пользователя: {str(e)}', 'danger')
            current_app.logger.error(f"Ошибка добавления пользователя: {e}")
            return render_template('add_user.html', form_data=request.form, all_groups=all_groups)
            
    return render_template('add_user.html', form_data={}, all_groups=all_groups)
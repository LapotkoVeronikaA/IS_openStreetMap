# app/utils.py
from flask import session, request, flash, redirect, url_for, current_app, g
from functools import wraps
from app.extensions import db
import requests
import os

USER_GROUPS = {
    'admin': {
        'name': 'Администратор',
        'is_deletable': False,
        'permissions': {
            'view_logs': True, 
            'manage_users': True,
            'view_organizations': True, 
            'manage_organizations': True,
            'view_map': True,
        }
    },
    'guest': {
        'name': 'Гость',
        'is_deletable': False,
        'permissions': {
             'view_map': True,
             'view_organizations': True,
        }
    }
}

def get_current_user_obj():
    from app.models import User
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

def manual_login_user(user):
    session.permanent = True
    session['user_id'] = user.id
    session['username'] = user.username
    session['logged_in'] = True

def manual_logout_user():
    session.clear()

def check_user_permission(permission_name):
    from app.models import Group
    user = get_current_user_obj()

    if user:
        if not user.group:
            return False
        if user.group.name == 'Администратор':
            return True
        user_permissions = {permission.name for permission in user.group.permissions}
        return permission_name in user_permissions
    else:
        if 'guest_permissions' not in g:
            guest_group = Group.query.filter_by(name='Гость').first()
            if guest_group:
                g.guest_permissions = {p.name for p in guest_group.permissions}
            else:
                g.guest_permissions = set()
        return permission_name in g.guest_permissions


def login_required_manual(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user_obj():
            flash('Для доступа к этой странице необходимо войти в систему.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def permission_required_manual(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_user_permission(permission_name):
                # Для гостей не показываем ошибку, а просим войти
                if not get_current_user_obj():
                    flash('Для выполнения этого действия необходимо войти в систему.', 'warning')
                    return redirect(url_for('auth.login', next=request.url))
                # Для залогиненных пользователей показываем ошибку прав
                flash('У вас нет прав для выполнения этого действия.', 'danger')
                return redirect(request.referrer or url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_user_activity(action, entity_type=None, entity_id=None, details_dict=None):
    from app.models import UserActivity
    user = get_current_user_obj()
    
    user_id_val = user.id if user else None
    username_val = user.username if user else "System/Unknown"

    ip_addr = request.remote_addr if request else 'N/A'
    
    activity = UserActivity(
        user_id=user_id_val,
        username=username_val,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_addr
    )

    if details_dict:
        activity.set_details(details_dict)

    db.session.add(activity)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при логировании действия '{action}': {e}")
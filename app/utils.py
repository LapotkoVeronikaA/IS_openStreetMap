# app/utils.py
from flask import session
from app.extensions import db

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

def check_user_permission(permission_name):
    return False # Заглушка

def manual_login_user(user):
    session.permanent = True
    session['user_id'] = user.id
    session['username'] = user.username
    session['logged_in'] = True

def manual_logout_user():
    session.clear()

def check_user_permission(permission_name):
    return False # Заглушка
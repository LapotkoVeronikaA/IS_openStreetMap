# app/auth/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import User
from app.utils import manual_login_user, manual_logout_user, log_user_activity, get_current_user_obj
from . import auth_bp
from urllib.parse import urlparse, urljoin

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user_obj():
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password_candidate = request.form.get('password')
        
        user_obj = User.query.filter_by(username=username).first()
        
        if user_obj and user_obj.password == password_candidate:
            manual_login_user(user_obj)
            log_user_activity(
                action="Пользователь вошел в систему", 
                entity_type="UserAuth", 
                entity_id=user_obj.id
            )
            flash('Вход выполнен успешно!', 'success')
            
            next_page = request.form.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            return redirect(url_for('main.dashboard'))
        else:
            log_user_activity(
                action="Неудачная попытка входа", 
                entity_type="UserAuth",
                details_dict={"username_attempt": username}
            )
            flash('Неверное имя пользователя или пароль.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    current_user = get_current_user_obj()
    if current_user:
        log_user_activity(
            action="Пользователь вышел из системы", 
            entity_type="UserAuth", 
            entity_id=current_user.id
        )
    manual_logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('auth.login'))
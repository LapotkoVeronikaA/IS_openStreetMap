# app/auth/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import User
from app.utils import manual_login_user, manual_logout_user, get_current_user_obj
from . import auth_bp

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
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    manual_logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('auth.login'))
# app/profile/routes.py
from flask import render_template, redirect, url_for, flash
from app.models import User
from app.utils import get_current_user_obj, permission_required_manual, login_required_manual, check_user_permission
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
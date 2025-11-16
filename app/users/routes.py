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
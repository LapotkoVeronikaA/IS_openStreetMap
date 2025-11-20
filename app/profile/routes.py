# app/profile/routes.py
from flask import render_template
from app.utils import login_required_manual
from . import profile_bp

@profile_bp.route('/')
@login_required_manual
def index():
    return "<h1>Личный кабинет</h1>"
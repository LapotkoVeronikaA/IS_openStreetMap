# app/profile/routes.py
from flask import render_template
from app.utils import permission_required_manual
from . import profile_bp

@profile_bp.route('/')
@permission_required_manual('view_profile')
def index():
    return "<h1>Личный кабинет</h1>"
# app/main/routes.py
from flask import Blueprint, render_template
from . import main_bp

@main_bp.route('/')
def dashboard():
    return "<h1>Привет на главной странице!</h1>"
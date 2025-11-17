# app/logs/routes.py
from flask import render_template, request
from app.models import UserActivity
from app.utils import permission_required_manual
from . import logs_bp
from sqlalchemy import func # для func.date
from datetime import datetime # для преобразования дат

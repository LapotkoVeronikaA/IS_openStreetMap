# logs/__init__.py
from flask import Blueprint
logs_bp = Blueprint('logs', __name__, template_folder='templates')
from . import routes
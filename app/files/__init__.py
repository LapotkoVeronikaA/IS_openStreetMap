# app/files/__init__.py
from flask import Blueprint
files_bp = Blueprint('files', __name__, template_folder='templates')
from . import routes
# app/generic_directory/__init__.py
from flask import Blueprint

generic_directory_bp = Blueprint('generic_directory', __name__, template_folder='templates')

from . import routes
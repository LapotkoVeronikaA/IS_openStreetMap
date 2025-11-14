# app/organizations/__init__.py
from flask import Blueprint

organizations_bp = Blueprint(
    'organizations', 
    __name__, 
    template_folder='templates'
)

from . import routes
from flask import Blueprint

groups_bp = Blueprint('groups', __name__, template_folder='templates')

from . import routes
# app/organizations/routes.py
from flask import render_template
from app.models import Organization
from app.utils import permission_required_manual
from . import organizations_bp

@organizations_bp.route('/')
@permission_required_manual('view_organizations')
def index():
    orgs = Organization.query.order_by(Organization.name).all()
    return render_template('organizations_index.html', organizations=orgs)
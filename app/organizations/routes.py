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

@organizations_bp.route('/<int:org_id>')
@permission_required_manual('view_organizations')
def view_org(org_id):
    org = Organization.query.get_or_404(org_id)
    return render_template('organization_public_view.html', org=org)
# app/organizations/routes.py
from flask import render_template, request, redirect, url_for, flash
from app.models import Organization
from app.extensions import db
from app.utils import permission_required_manual, log_user_activity
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

@organizations_bp.route('/add', methods=['GET', 'POST'])
@permission_required_manual('manage_organizations')
def add_org():
    if request.method == 'POST':
        if not request.form.get('name') or not request.form.get('location'):
            flash('Поля "Название" и "Адрес" являются обязательными.', 'danger')
            return render_template('organization_form.html', form_data=request.form)

        new_org = Organization(
            name=request.form.get('name'),
            legal_name=request.form.get('legal_name'),
            org_type=request.form.get('org_type'),
            location=request.form.get('location'),
            head_of_organization=request.form.get('head_of_organization'),
            website=request.form.get('website'),
            main_phone=request.form.get('main_phone'),
            main_email=request.form.get('main_email'),
            notes=request.form.get('notes'),
        )
        db.session.add(new_org)
        db.session.commit()
        
        log_user_activity(f"Добавлена организация: {new_org.name}", "Organization", new_org.id)
        flash('Организация успешно добавлена.', 'success')
        return redirect(url_for('organizations.index'))
            
    return render_template('organization_form.html', form_data={})


@organizations_bp.route('/edit/<int:org_id>', methods=['GET', 'POST'])
@permission_required_manual('manage_organizations')
def edit_org(org_id):
    org = Organization.query.get_or_404(org_id)
    if request.method == 'POST':
        if not request.form.get('name') or not request.form.get('location'):
            flash('Поля "Название" и "Адрес" являются обязательными.', 'danger')
            return render_template('organization_form.html', org=org)

        org.name = request.form.get('name')
        org.legal_name = request.form.get('legal_name')
        org.org_type = request.form.get('org_type')
        org.location = request.form.get('location')
        org.head_of_organization = request.form.get('head_of_organization')
        org.website = request.form.get('website')
        org.main_phone = request.form.get('main_phone')
        org.main_email = request.form.get('main_email')
        org.notes = request.form.get('notes')
        
        db.session.commit()
        log_user_activity(f"Отредактирована организация: {org.name}", "Organization", org.id)
        flash('Организация успешно обновлена.', 'success')
        return redirect(url_for('organizations.view_org', org_id=org.id))
            
    return render_template('organization_form.html', org=org)
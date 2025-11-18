# app/organizations/routes.py
import os
import shutil
import uuid
import io
import re
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify, send_file
from werkzeug.utils import secure_filename
from app.models import Organization, GenericDirectoryItem
from app.extensions import db
from app.utils import permission_required_manual, log_user_activity, geocode_location
from . import organizations_bp

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files_for_org(org_id, subfolder):
    file_urls = []
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'organizations', str(org_id), subfolder)
    
    if os.path.exists(upload_folder):
        for filename in sorted(os.listdir(upload_folder)):
            if '.' in filename:
                file_urls.append(url_for('static', filename=f'uploads/organizations/{org_id}/{subfolder}/{filename}'))
    return file_urls

@organizations_bp.route('/')
@permission_required_manual('view_organizations')
def index():
    orgs = Organization.query.order_by(Organization.name).all()
    return render_template('organizations_index.html', organizations=orgs)

@organizations_bp.route('/<int:org_id>')
@permission_required_manual('view_organizations')
def view_org(org_id):
    org = Organization.query.get_or_404(org_id)
    photos = get_files_for_org(org_id, 'photos')
    floor_plans = get_files_for_org(org_id, 'floor_plans')
    return render_template('organization_public_view.html', org=org, photos=photos, floor_plans=floor_plans)


@organizations_bp.route('/add', methods=['GET', 'POST'])
@permission_required_manual('manage_organizations')
def add_org():
    faculty_names = GenericDirectoryItem.query.filter_by(directory_type='faculty_names').order_by(GenericDirectoryItem.name).all()
    department_names = GenericDirectoryItem.query.filter_by(directory_type='department_names').order_by(GenericDirectoryItem.name).all()
    organization_types = GenericDirectoryItem.query.filter_by(directory_type='organization_types').order_by(GenericDirectoryItem.name).all()

    if request.method == 'POST':
        location_str = request.form.get('location')
        if not request.form.get('name') or not location_str:
            flash('Поля "Название" и "Адрес" являются обязательными.', 'danger')
            return render_template('organization_form.html', org=None, form_data=request.form, photos=[], floor_plans=[], faculty_names=faculty_names, department_names=department_names, organization_types=organization_types)

        lat, lon = geocode_location(location_str)

        new_org = Organization(
            name=request.form.get('name'),
            legal_name=request.form.get('legal_name'),
            org_type=request.form.get('org_type'),
            location=location_str,
            head_of_organization=request.form.get('head_of_organization'),
            website=request.form.get('website'),
            main_phone=request.form.get('main_phone'),
            main_email=request.form.get('main_email'),
            notes=request.form.get('notes'),
            latitude=lat,
            longitude=lon
        )
        
        new_org.set_contacts([{"full_name": n, "position": p, "phone": ph} for n, p, ph in zip(request.form.getlist('contact_full_name'), request.form.getlist('contact_position'), request.form.getlist('contact_phone')) if n.strip()])
        new_org.set_departments([{"faculty": f, "department": d, "employee_count": c} for f, d, c in zip(request.form.getlist('department_faculty'), request.form.getlist('department_name'), request.form.getlist('department_employee_count')) if f.strip() or d.strip()])

        db.session.add(new_org)
        db.session.commit()

        for subfolder, file_list in [('photos', request.files.getlist('photos')), ('floor_plans', request.files.getlist('floor_plans'))]:
            if file_list and file_list[0].filename:
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'organizations', str(new_org.id), subfolder)
                os.makedirs(upload_folder, exist_ok=True)
                for file in file_list:
                    if file and allowed_file(file.filename):
                        ext = file.filename.rsplit('.', 1)[1].lower()
                        filename = f"{uuid.uuid4()}.{ext}"
                        file.save(os.path.join(upload_folder, filename))
        
        log_user_activity(f"Добавлена организация: {new_org.name}", "Organization", new_org.id)
        flash('Организация успешно добавлена.', 'success')
        return redirect(url_for('organizations.index'))
            
    return render_template('organization_form.html', org=None, form_data={}, photos=[], floor_plans=[], faculty_names=faculty_names, department_names=department_names, organization_types=organization_types)


@organizations_bp.route('/edit/<int:org_id>', methods=['GET', 'POST'])
@permission_required_manual('manage_organizations')
def edit_org(org_id):
    org = Organization.query.get_or_404(org_id)
    faculty_names = GenericDirectoryItem.query.filter_by(directory_type='faculty_names').order_by(GenericDirectoryItem.name).all()
    department_names = GenericDirectoryItem.query.filter_by(directory_type='department_names').order_by(GenericDirectoryItem.name).all()
    organization_types = GenericDirectoryItem.query.filter_by(directory_type='organization_types').order_by(GenericDirectoryItem.name).all()
    
    if request.method == 'POST':
        new_location_str = request.form.get('location')
        if not request.form.get('name') or not new_location_str:
            flash('Поля "Название" и "Адрес" являются обязательными.', 'danger')
            return render_template('organization_form.html', org=org, photos=get_files_for_org(org_id, 'photos'), floor_plans=get_files_for_org(org_id, 'floor_plans'), faculty_names=faculty_names, department_names=department_names, organization_types=organization_types)

        if org.location != new_location_str:
            lat, lon = geocode_location(new_location_str)
            org.latitude = lat
            org.longitude = lon
        
        org.name = request.form.get('name')
        org.legal_name = request.form.get('legal_name')
        org.org_type = request.form.get('org_type')
        org.location = new_location_str
        org.head_of_organization = request.form.get('head_of_organization')
        org.website = request.form.get('website')
        org.main_phone = request.form.get('main_phone')
        org.main_email = request.form.get('main_email')
        org.notes = request.form.get('notes')
        
        org.set_contacts([{"full_name": n, "position": p, "phone": ph} for n, p, ph in zip(request.form.getlist('contact_full_name'), request.form.getlist('contact_position'), request.form.getlist('contact_phone')) if n.strip()])
        org.set_departments([{"faculty": f, "department": d, "employee_count": c} for f, d, c in zip(request.form.getlist('department_faculty'), request.form.getlist('department_name'), request.form.getlist('department_employee_count')) if f.strip() or d.strip()])

        for subfolder, file_list in [('photos', request.files.getlist('photos')), ('floor_plans', request.files.getlist('floor_plans'))]:
            if file_list and file_list[0].filename:
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'organizations', str(org_id), subfolder)
                os.makedirs(upload_folder, exist_ok=True)
                for file in file_list:
                    if file and allowed_file(file.filename):
                        ext = file.filename.rsplit('.', 1)[1].lower()
                        filename = f"{uuid.uuid4()}.{ext}"
                        file.save(os.path.join(upload_folder, filename))
        
        db.session.commit()
        log_user_activity(f"Отредактирована организация: {org.name}", "Organization", org.id)
        flash('Организация успешно обновлена.', 'success')
        return redirect(url_for('organizations.index'))
            
    photos = get_files_for_org(org_id, 'photos')
    floor_plans = get_files_for_org(org_id, 'floor_plans')
    return render_template('organization_form.html', org=org, form_data=org, photos=photos, floor_plans=floor_plans, faculty_names=faculty_names, department_names=department_names, organization_types=organization_types)


@organizations_bp.route('/delete_file/<int:org_id>/<string:subfolder>/<string:filename>', methods=['POST'])
@permission_required_manual('manage_organizations')
def delete_file(org_id, subfolder, filename):
    if subfolder not in ['photos', 'floor_plans']:
        return jsonify({'success': False, 'message': 'Неверный тип файла.'}), 400

    filename = secure_filename(filename)
    file_path = os.path.join(current_app.static_folder, 'uploads', 'organizations', str(org_id), subfolder, filename)
    
    if os.path.exists(file_path):
        try:
            org = Organization.query.get_or_404(org_id)
            os.remove(file_path)
            log_user_activity(f"Удален файл '{filename}' для организации: {org.name}", "Organization", org_id)
            return jsonify({'success': True, 'message': 'Файл удален.'})
        except Exception as e:
            current_app.logger.error(f"Ошибка удаления файла {file_path}: {e}")
            return jsonify({'success': False, 'message': 'Ошибка при удалении файла.'}), 500
    else:
        return jsonify({'success': False, 'message': 'Файл не найден.'}), 404

@organizations_bp.route('/delete/<int:org_id>', methods=['POST'])
@permission_required_manual('manage_organizations')
def delete_org(org_id):
    org = Organization.query.get_or_404(org_id)
    org_name_deleted = org.name
    
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'organizations', str(org_id))
    if os.path.exists(upload_folder):
        shutil.rmtree(upload_folder)

    db.session.delete(org)
    db.session.commit()
    log_user_activity(f"Удалена организация: {org_name_deleted}", "Organization", org_id)
    flash('Организация успешно удалена.', 'success')
    return redirect(url_for('organizations.index'))
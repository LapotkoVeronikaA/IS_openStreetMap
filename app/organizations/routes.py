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
from docx import Document
from docx.shared import Inches
import openpyxl
from openpyxl.styles import Font, Alignment

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

def sanitize_for_filename(text):
    # Удаляем недопустимые символы и заменяем пробелы на подчеркивания
    sanitized = re.sub(r'[\\/*?:"<>|]', "", text)
    sanitized = sanitized.replace(" ", "_")
    return sanitized if sanitized else "organization_report"

@organizations_bp.route('/export/docx/<int:org_id>')
def export_docx(org_id):
    org = Organization.query.get_or_404(org_id)
    
    document = Document()
    document.add_heading(f'Карточка организации: {org.name}', 0)

    p = document.add_paragraph()
    p.add_run('Юридическое название: ').bold = True
    p.add_run(org.legal_name or 'Не указано')

    p = document.add_paragraph()
    p.add_run('Адрес: ').bold = True
    p.add_run(org.location or 'Не указано')
    
    p = document.add_paragraph()
    p.add_run('Руководитель: ').bold = True
    p.add_run(org.head_of_organization or 'Не указано')

    document.add_heading('Контакты', level=1)
    if org.get_contacts():
        for contact in org.get_contacts():
            document.add_paragraph(
                f"{contact.get('full_name', '')} ({contact.get('position', '-')}) - {contact.get('phone', '-')}", style='List Bullet'
            )
    else:
        document.add_paragraph('Нет данных.')

    document.add_heading('Структура', level=1)
    if org.get_departments():
        table = document.add_table(rows=1, cols=3)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Факультет/Управление'
        hdr_cells[1].text = 'Отдел/Кафедра'
        hdr_cells[2].text = 'Кол-во сотрудников'
        for dept in org.get_departments():
            row_cells = table.add_row().cells
            row_cells[0].text = dept.get('faculty', '')
            row_cells[1].text = dept.get('department', '')
            row_cells[2].text = str(dept.get('employee_count', ''))
    else:
        document.add_paragraph('Нет данных.')

    f = io.BytesIO()
    document.save(f)
    f.seek(0)
    
    filename = f"{sanitize_for_filename(org.name)}.docx"
    return send_file(f, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

@organizations_bp.route('/export/xlsx/<int:org_id>')
def export_xlsx(org_id):
    org = Organization.query.get_or_404(org_id)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Карточка организации"

    bold_font = Font(bold=True)
    
    ws.merge_cells('A1:B1')
    ws['A1'] = f"Карточка организации: {org.name}"
    ws['A1'].font = Font(bold=True, size=16)

    data = [
        ("Название", org.name), ("Юридическое название", org.legal_name),
        ("Тип", org.org_type), ("Адрес", org.location),
        ("Руководитель", org.head_of_organization), ("Сайт", org.website),
        ("Телефон", org.main_phone), ("Email", org.main_email), ("Заметки", org.notes)
    ]
    for row_idx, (key, value) in enumerate(data, 3):
        ws[f'A{row_idx}'] = key
        ws[f'A{row_idx}'].font = bold_font
        ws[f'B{row_idx}'] = value

    start_row = len(data) + 5
    ws[f'A{start_row}'] = "Контакты"
    ws[f'A{start_row}'].font = Font(bold=True, size=14)
    headers = ["ФИО", "Должность", "Телефон"]
    ws.append(headers)
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=start_row + 1, column=col_idx).font = bold_font

    for contact in org.get_contacts():
        ws.append([contact.get('full_name'), contact.get('position'), contact.get('phone')])

    start_row = ws.max_row + 2
    ws[f'A{start_row}'] = "Структура"
    ws[f'A{start_row}'].font = Font(bold=True, size=14)
    headers = ["Факультет/Управление", "Отдел/Кафедра", "Кол-во сотрудников"]
    ws.append(headers)
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=start_row + 1, column=col_idx).font = bold_font

    for dept in org.get_departments():
        ws.append([dept.get('faculty'), dept.get('department'), dept.get('employee_count')])
    
    for column_cells in ws.columns:
        # Пропускаем объединенные ячейки, чтобы избежать ошибки
        if isinstance(column_cells[0], openpyxl.cell.cell.MergedCell):
            continue
        length = max(len(str(cell.value or "")) for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2

    f = io.BytesIO()
    wb.save(f)
    f.seek(0)

    filename = f"{sanitize_for_filename(org.name)}.xlsx"
    return send_file(f, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
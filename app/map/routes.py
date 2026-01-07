# app/map/routes.py
from flask import render_template, url_for, jsonify, flash, redirect
from app.models import Organization
from app.utils import check_user_permission, permission_required_manual
from app.organizations.routes import get_files_for_org
from . import map_bp
import re

@map_bp.route('/')
@permission_required_manual('view_map')
def show_map():
    markers_data = []

    organizations = Organization.query.filter(
        Organization.latitude.isnot(None),
        Organization.longitude.isnot(None)
    ).order_by(Organization.name).all()

    # Собираем уникальные типы для фильтров
    org_types = sorted(list(set(o.org_type for o in organizations if o.org_type)))

    for org in organizations:
        # Упрощаем ключ для иконки
        icon_key = re.sub(r'[^а-яА-Я0-9]', '', org.org_type) if org.org_type else "default"

        # Формируем список отделов (детей) вручную для JSON
        children_list = []
        for child in org.children:
            children_list.append({
                'name': child.name,
                'org_type': child.org_type,
                'employee_count': child.total_employee_count
            })

        markers_data.append({
            "id": org.id,
            "lat": org.latitude,
            "lon": org.longitude,
            "name": org.name,
            "icon_key": icon_key,
            "filter_data": {
                "org_type": org.org_type,
                "head": org.head_of_organization,
            },
            "details": {
                'name': org.name,
                'location': org.location,
                'org_type': org.org_type or '-',
                'legal_name': org.legal_name or '-',
                'head_of_organization': org.head_of_organization or '-',
                'website': org.website_url, 
                'main_phone': org.main_phone,
                'main_email': org.main_email,
                'total_employees': org.total_employee_count,
                'departments': children_list, 
                'contacts': org.get_contacts(),
                'photos': get_files_for_org(org.id, 'photos'),
                'floor_plans': get_files_for_org(org.id, 'floor_plans'),
                
                # ссылки для интерфейса (включая отчеты)
                'edit_url': url_for('organizations.edit_org', org_id=org.id),
                'view_url': url_for('organizations.view_org', org_id=org.id),
                'export_docx_url': url_for('organizations.export_docx', org_id=org.id),
                'export_xlsx_url': url_for('organizations.export_xlsx', org_id=org.id)
            }
        })
    
    user_perms = {
        'can_manage_organizations': check_user_permission('manage_organizations')
    }

    return render_template(
        'map.html', 
        markers_data=markers_data,
        user_perms=user_perms,
        org_types=org_types
    )
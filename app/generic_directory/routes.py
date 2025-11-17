# app/generic_directory/routes.py
from flask import render_template, request, redirect, url_for, flash
from sqlalchemy import func
from app.models import GenericDirectoryItem
from app.extensions import db
from app.utils import permission_required_manual, log_user_activity
from . import generic_directory_bp

# === КОНФИГУРАЦИЯ СПРАВОЧНИКОВ ===
DIRECTORY_CONFIG = {
    'organization_types': {
        'name': 'Типы организаций',
        'icon': 'fa-building-columns'
    },
    'faculty_names': {
        'name': 'Факультеты / Управления',
        'icon': 'fa-university'
    },
    'department_names': {
        'name': 'Отделы / Кафедры',
        'icon': 'fa-users-cog'
    },
    'district_names': {
        'name': 'Округа',
        'icon': 'fa-map-pin'
    },
}

@generic_directory_bp.route('/')
@permission_required_manual('manage_organizations')
def index():
    """Отображает страницу со всеми общими справочниками."""
    all_items = GenericDirectoryItem.query.order_by(func.lower(GenericDirectoryItem.name)).all()
    
    # Группируем элементы по типу справочника
    directories = {dir_type: [] for dir_type in DIRECTORY_CONFIG.keys()}
    for item in all_items:
        if item.directory_type in directories:
            directories[item.directory_type].append(item)
            
    return render_template(
        'generic_directories_index.html', 
        directories=directories, 
        DIRECTORY_CONFIG=DIRECTORY_CONFIG
    )

@generic_directory_bp.route('/add', methods=['POST'])
@permission_required_manual('manage_organizations')
def add_item():
    """Добавляет новый элемент в справочник."""
    dir_type = request.form.get('directory_type')
    name = request.form.get('name', '').strip()

    if not all([dir_type, name]):
        flash('Необходимо указать тип справочника и название элемента.', 'danger')
        return redirect(url_for('generic_directory.index'))

    if dir_type not in DIRECTORY_CONFIG:
        flash('Указан неверный тип справочника.', 'danger')
        return redirect(url_for('generic_directory.index'))

    # Проверка на дубликат
    existing = GenericDirectoryItem.query.filter_by(directory_type=dir_type, name=name).first()
    if existing:
        flash(f'Элемент "{name}" уже существует в справочнике "{DIRECTORY_CONFIG[dir_type]["name"]}".', 'warning')
        return redirect(url_for('generic_directory.index'))
        
    try:
        new_item = GenericDirectoryItem(directory_type=dir_type, name=name)
        db.session.add(new_item)
        db.session.commit()
        log_user_activity(
            f"Добавлен элемент в справочник '{DIRECTORY_CONFIG[dir_type]['name']}': {name}",
            "GenericDirectory", new_item.id
        )
        flash('Элемент успешно добавлен.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении элемента: {e}', 'danger')

    return redirect(url_for('generic_directory.index'))

@generic_directory_bp.route('/edit/<int:item_id>', methods=['POST'])
@permission_required_manual('manage_organizations')
def edit_item(item_id):
    """Редактирует существующий элемент справочника."""
    item = GenericDirectoryItem.query.get_or_404(item_id)
    old_name = item.name
    new_name = request.form.get('name', '').strip()

    if not new_name:
        flash('Название элемента не может быть пустым.', 'danger')
        return redirect(url_for('generic_directory.index'))

    # Проверка на дубликат (исключая сам редактируемый элемент)
    existing = GenericDirectoryItem.query.filter(
        GenericDirectoryItem.directory_type == item.directory_type,
        GenericDirectoryItem.name == new_name,
        GenericDirectoryItem.id != item_id
    ).first()

    if existing:
        flash(f'Элемент "{new_name}" уже существует в этом справочнике.', 'warning')
        return redirect(url_for('generic_directory.index'))

    try:
        item.name = new_name
        db.session.commit()
        log_user_activity(
            f"Изменен элемент в справочнике '{DIRECTORY_CONFIG[item.directory_type]['name']}'",
            "GenericDirectory", item.id,
            details_dict={'name': {'old': old_name, 'new': new_name}}
        )
        flash('Элемент успешно обновлен.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении элемента: {e}', 'danger')
        
    return redirect(url_for('generic_directory.index'))

@generic_directory_bp.route('/delete/<int:item_id>', methods=['POST'])
@permission_required_manual('manage_organizations')
def delete_item(item_id):
    """Удаляет элемент из справочника."""
    item = GenericDirectoryItem.query.get_or_404(item_id)
    item_name, dir_name = item.name, DIRECTORY_CONFIG[item.directory_type]['name']
    
    try:
        db.session.delete(item)
        db.session.commit()
        log_user_activity(f"Удален элемент из справочника '{dir_name}': {item_name}", "GenericDirectory", item_id)
        flash(f'Элемент "{item_name}" успешно удален.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении элемента: {e}', 'danger')
        
    return redirect(url_for('generic_directory.index'))
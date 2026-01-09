# app/generic_directory/routes.py
from flask import render_template, request, redirect, url_for, flash
from sqlalchemy import func
from app.models import GenericDirectoryItem
from app.extensions import db
from app.utils import permission_required_manual, log_user_activity
from . import generic_directory_bp

# === КОНФИГУРАЦИЯ СПРАВОЧНИКОВ ===
DIRECTORY_CONFIG = {
    'org_type': {
        'name': 'Типы организаций',
        'icon': 'fa-tags'
    }
}

@generic_directory_bp.route('/')
@permission_required_manual('manage_organizations')
def index():
    """Отображает страницу управления справочником типов."""
    all_items = GenericDirectoryItem.query.filter_by(directory_type='org_type').order_by(func.lower(GenericDirectoryItem.name)).all()
    
    # Группируем для шаблона
    directories = {'org_type': all_items}
            
    return render_template(
        'generic_directories_index.html', 
        directories=directories, 
        DIRECTORY_CONFIG=DIRECTORY_CONFIG
    )

@generic_directory_bp.route('/add', methods=['POST'])
@permission_required_manual('manage_organizations')
def add_item():
    """Добавляет новый тип в справочник."""
    dir_type = 'org_type'
    name = request.form.get('name', '').strip()

    if not name:
        flash('Необходимо указать название типа.', 'danger')
        return redirect(url_for('generic_directory.index'))

    # Проверка на дубликат
    existing = GenericDirectoryItem.query.filter_by(directory_type=dir_type, name=name).first()
    if existing:
        flash(f'Тип "{name}" уже существует в справочнике.', 'warning')
        return redirect(url_for('generic_directory.index'))
        
    try:
        new_item = GenericDirectoryItem(directory_type=dir_type, name=name)
        db.session.add(new_item)
        db.session.commit()
        log_user_activity(
            f"Добавлен новый тип организации: {name}",
            "GenericDirectory", new_item.id
        )
        flash('Новый тип успешно добавлен.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении: {e}', 'danger')

    return redirect(url_for('generic_directory.index'))

@generic_directory_bp.route('/edit/<int:item_id>', methods=['POST'])
@permission_required_manual('manage_organizations')
def edit_item(item_id):
    """Редактирует существующий тип."""
    item = GenericDirectoryItem.query.get_or_404(item_id)
    old_name = item.name
    new_name = request.form.get('name', '').strip()

    if not new_name:
        flash('Название не может быть пустым.', 'danger')
        return redirect(url_for('generic_directory.index'))

    existing = GenericDirectoryItem.query.filter(
        GenericDirectoryItem.directory_type == 'org_type',
        GenericDirectoryItem.name == new_name,
        GenericDirectoryItem.id != item_id
    ).first()

    if existing:
        flash(f'Тип "{new_name}" уже существует.', 'warning')
        return redirect(url_for('generic_directory.index'))

    try:
        item.name = new_name
        db.session.commit()
        log_user_activity(
            f"Изменено название типа организации",
            "GenericDirectory", item.id,
            details_dict={'name': {'old': old_name, 'new': new_name}}
        )
        flash('Тип успешно обновлен.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении: {e}', 'danger')
        
    return redirect(url_for('generic_directory.index'))

@generic_directory_bp.route('/delete/<int:item_id>', methods=['POST'])
@permission_required_manual('manage_organizations')
def delete_item(item_id):
    """Удаляет тип из справочника."""
    item = GenericDirectoryItem.query.get_or_404(item_id)
    item_name = item.name
    
    try:
        db.session.delete(item)
        db.session.commit()
        log_user_activity(f"Удален тип организации: {item_name}", "GenericDirectory", item_id)
        flash(f'Тип "{item_name}" удален.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {e}', 'danger')
        
    return redirect(url_for('generic_directory.index'))
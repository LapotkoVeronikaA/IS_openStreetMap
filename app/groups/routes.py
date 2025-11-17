from flask import render_template, request, redirect, url_for, flash
from app.models import Group, Permission, User
from app.extensions import db
from app.utils import log_user_activity, permission_required_manual
from . import groups_bp

def categorize_permissions(permissions):
    """Categorizes permissions into groups for display."""
    categories = {
        'Справочник': [],
        'Администрирование': [],
        'Прочее': []
    }
    mapping = {
        'Справочник': ['view_directory', 'manage_directory'],
        'Администрирование': ['manage_users', 'manage_groups', 'view_logs'],
    }
    perm_to_cat = {}
    for cat, perms in mapping.items():
        for perm in perms:
            perm_to_cat[perm] = cat

    for p in permissions:
        category = perm_to_cat.get(p.name, 'Прочее')
        categories[category].append(p)

    return {k: v for k, v in categories.items() if v}

@groups_bp.route('/')
@permission_required_manual('manage_groups')
def index():
    """Отображает список всех групп и их прав."""
    groups = Group.query.options(db.selectinload(Group.permissions)).order_by(Group.name).all()
    return render_template('groups_index.html', groups=groups)

@groups_bp.route('/add', methods=['GET', 'POST'])
@permission_required_manual('manage_groups')
def add_group():
    """Форма для создания новой группы."""
    if request.method == 'POST':
        group_name = request.form.get('name', '').strip()
        if not group_name:
            flash('Название группы не может быть пустым.', 'danger')
        elif Group.query.filter(Group.name.ilike(group_name)).first():
            flash('Группа с таким названием уже существует.', 'danger')
        else:
            try:
                new_group = Group(name=group_name)
                permission_ids = request.form.getlist('permissions', type=int)
                if permission_ids:
                    permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
                    new_group.permissions = permissions
                
                db.session.add(new_group)
                db.session.commit()

                log_user_activity(f"Создана группа: {group_name}", "Group", new_group.id)
                flash('Группа успешно создана.', 'success')
                return redirect(url_for('groups.index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при создании группы: {e}', 'danger')

    all_permissions = Permission.query.order_by(Permission.description).all()
    categorized_permissions = categorize_permissions(all_permissions)
    return render_template('group_form.html', group=None, categorized_permissions=categorized_permissions, selected_permissions=set())

@groups_bp.route('/edit/<int:group_id>', methods=['GET', 'POST'])
@permission_required_manual('manage_groups')
def edit_group(group_id):
    """Форма для редактирования группы."""
    group = Group.query.get_or_404(group_id)
    
    if request.method == 'POST':
        group_name = request.form.get('name', '').strip()
        if not group_name:
            flash('Название группы не может быть пустым.', 'danger')
        else:
            try:
                group.name = group_name
                permission_ids = request.form.getlist('permissions', type=int)
                group.permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()

                db.session.commit()
                log_user_activity(f"Отредактирована группа: {group_name}", "Group", group.id)
                flash('Группа успешно обновлена.', 'success')
                return redirect(url_for('groups.index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при обновлении группы: {e}', 'danger')

    all_permissions = Permission.query.order_by(Permission.description).all()
    categorized_permissions = categorize_permissions(all_permissions)
    selected_permissions = {p.id for p in group.permissions}
    return render_template('group_form.html', group=group, categorized_permissions=categorized_permissions, selected_permissions=selected_permissions)

@groups_bp.route('/delete/<int:group_id>', methods=['POST'])
@permission_required_manual('manage_groups')
def delete_group(group_id):
    """Удаление группы."""
    group = Group.query.get_or_404(group_id)

    if not group.is_deletable:
        flash('Эту группу нельзя удалить.', 'danger')
        return redirect(url_for('groups.index'))

    if User.query.filter_by(group_id=group_id).first():
        flash('Нельзя удалить группу, в которой есть пользователи. Сначала перенесите их в другую группу.', 'warning')
        return redirect(url_for('groups.index'))
        
    try:
        group_name = group.name
        db.session.delete(group)
        db.session.commit()
        log_user_activity(f"Удалена группа: {group_name}", "Group", group_id)
        flash(f'Группа "{group_name}" успешно удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении группы: {e}', 'danger')

    return redirect(url_for('groups.index'))
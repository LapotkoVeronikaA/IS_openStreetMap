# app/api/routes.py
from functools import wraps
from flask import jsonify, request, current_app
from . import api_bp
from app.models import Organization, User, Group, GenericDirectoryItem

# Декоратор для проверки API-ключа
def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key or api_key != current_app.config['API_SECRET_KEY']:
            return jsonify({'message': 'Ошибка: неверный или отсутствующий API-ключ'}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/v1/organizations', methods=['GET'])
@api_key_required
def get_organizations():
    """
    Возвращает список всех организаций из реестра.
    """
    try:
        orgs = Organization.query.order_by(Organization.name).all()
        
        results = []
        for org in orgs:
            results.append({
                'id': org.id,
                'name': org.name,
                'type': org.org_type,
                'location': org.location,
                'head_of_organization': org.head_of_organization,
                'latitude': org.latitude,
                'longitude': org.longitude,
                'contacts': org.get_contacts(),
                'departments': org.get_departments(),
                'website': org.website
            })
            
        return jsonify(results)

    except Exception as e:
        current_app.logger.error(f"API Error in get_organizations: {e}")
        return jsonify({'message': 'Внутренняя ошибка сервера'}), 500

@api_bp.route('/v1/users-groups', methods=['GET'])
@api_key_required
def get_users_and_groups():
    """Возвращает список групп, а затем пользователей."""
    try:
        groups = Group.query.all()
        users = User.query.all()

        groups_data = [{'id': g.id, 'name': g.name} for g in groups]
        users_data = [{
            'id': u.id,
            'username': u.username,
            'full_name': u.full_name,
            'department': u.department,
            'position': u.position,
            'group_name': u.group.name if u.group else None
        } for u in users]

        return jsonify({
            'groups': groups_data,
            'users': users_data
        })
    except Exception as e:
        current_app.logger.error(f"API Error in get_users_and_groups: {e}")
        return jsonify({'message': 'Внутренняя ошибка сервера'}), 500

@api_bp.route('/v1/generic-directory-items', methods=['GET'])
@api_key_required
def get_generic_directory_items():
    """Возвращает все элементы общих справочников."""
    try:
        items = GenericDirectoryItem.query.all()
        items_data = [{
            'id': item.id,
            'directory_type': item.directory_type,
            'name': item.name
        } for item in items]
        return jsonify(items_data)
    except Exception as e:
        current_app.logger.error(f"API Error in get_generic_directory_items: {e}")
        return jsonify({'message': 'Внутренняя ошибка сервера'}), 500
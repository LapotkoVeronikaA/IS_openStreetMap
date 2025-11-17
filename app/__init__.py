# app/__init__.py
from flask import Flask
from .config import Config
from .extensions import db, migrate

from .utils import USER_GROUPS, get_current_user_obj, check_user_permission

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)

    # Регистрация блюпринтов
    from .main import main_bp
    app.register_blueprint(main_bp)
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from .users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')
    from .logs import logs_bp
    app.register_blueprint(logs_bp, url_prefix='/logs')
    from .organizations import organizations_bp
    app.register_blueprint(organizations_bp, url_prefix='/organizations')
    from .groups import groups_bp
    app.register_blueprint(groups_bp, url_prefix='/groups')
    from .generic_directory import generic_directory_bp
    app.register_blueprint(generic_directory_bp, url_prefix='/generic-directories')


    @app.context_processor
    def inject_global_vars():
        return dict(
            current_user_obj=get_current_user_obj, 
            check_user_permission=check_user_permission
        )

    @app.cli.command("create-admin")
    def create_admin_command():
        """Создает пользователя admin по умолчанию."""
        from .models import User, Group
        with app.app_context():
            if User.query.filter_by(username='admin').first():
                print("Пользователь admin уже существует.")
                return
            
            admin_group = Group.query.filter_by(name='Администратор').first()
            if not admin_group:
                print("Группа 'Администратор' не найдена. Запустите 'flask seed-permissions' для первоначального заполнения.")
                return
            
            admin = User(username='admin', password='admin', group_id=admin_group.id, full_name='Администратор системы')
            db.session.add(admin)
            db.session.commit()
            print("Пользователь admin создан.")

    @app.cli.command("seed-permissions")
    def seed_permissions_command():
        """Создает и/или обновляет группы и права на основе словаря USER_GROUPS."""
        from .models import Group, Permission
        from .utils import USER_GROUPS 

        with app.app_context():
            print("Синхронизация групп и прав...")
            
            # Шаг 1: Создание или обновление групп
            group_objects = {}
            for group_key, group_info in USER_GROUPS.items():
                group_obj = Group.query.filter_by(name=group_info['name']).first()
                if not group_obj:
                    group_obj = Group(
                        name=group_info['name'],
                        is_deletable=group_info.get('is_deletable', True)
                    )
                    db.session.add(group_obj)
                group_objects[group_info['name']] = group_obj
            db.session.commit()
            print(f"Найдено/создано {len(group_objects)} групп.")

            # Шаг 2: Сбор и создание всех возможных прав
            all_permission_names = set()
            for group_info in USER_GROUPS.values():
                for perm in group_info['permissions']:
                    all_permission_names.add(perm)

            permission_descriptions = {
                'view_logs': 'Просматривать журнал действий',
                'manage_users': 'Управлять пользователями',
                'view_organizations': 'Просматривать реестр организаций',
                'manage_organizations': 'Управлять реестром организаций',
                'view_map': 'Просматривать интерактивную карту',
            }

            permission_objects = {}
            for perm_name in sorted(list(all_permission_names)):
                perm_obj = Permission.query.filter_by(name=perm_name).first()
                if not perm_obj:
                    perm_obj = Permission(
                        name=perm_name,
                        description=permission_descriptions.get(perm_name, 'Нет описания')
                    )
                    db.session.add(perm_obj)
                permission_objects[perm_name] = perm_obj
            db.session.commit()
            print(f"Найдено/создано {len(permission_objects)} прав.")

            # Шаг 3: Назначение прав группам
            for group_name, group_obj in group_objects.items():
                group_key = next((key for key, info in USER_GROUPS.items() if info['name'] == group_name), None)
                if group_key:
                    group_info = USER_GROUPS[group_key]
                    
                    # Очищаем старые права и добавляем новые
                    group_obj.permissions.clear()
                    for perm_name, has_perm in group_info.get('permissions', {}).items():
                        if has_perm and perm_name in permission_objects:
                            group_obj.permissions.append(permission_objects[perm_name])
            
            db.session.commit()
            print("Права успешно назначены группам.")
            print("Синхронизация завершена.")

    return app
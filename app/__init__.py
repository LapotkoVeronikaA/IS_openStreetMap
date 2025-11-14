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

    from .organizations import organizations_bp
    app.register_blueprint(organizations_bp, url_prefix='/organizations')

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
            
            group_objects = {}
            for group_key, group_info in USER_GROUPS.items():
                group_obj = Group.query.filter_by(name=group_info['name']).first()
                if not group_obj:
                    group_obj = Group(name=group_info['name'], is_deletable=group_info.get('is_deletable', True))
                    db.session.add(group_obj)
                group_objects[group_info['name']] = group_obj
            db.session.commit()

            all_permission_names = {'view_organizations', 'manage_organizations', 'manage_users', 'view_logs', 'view_map'}
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
                    perm_obj = Permission(name=perm_name, description=permission_descriptions.get(perm_name, 'Нет описания'))
                    db.session.add(perm_obj)
                permission_objects[perm_name] = perm_obj
            db.session.commit()

            print("Синхронизация завершена.")

    return app
# app/__init__.py
from flask import Flask
from .config import Config
from .extensions import db, migrate
from .utils import USER_GROUPS, get_current_user_obj, check_user_permission
import jinja2

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Включение расширения 'do' для Jinja2
    app.jinja_env.add_extension('jinja2.ext.do')
    
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
    from .map import map_bp
    app.register_blueprint(map_bp, url_prefix='/map')
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    from .profile import profile_bp
    app.register_blueprint(profile_bp, url_prefix='/profile')


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
                print("Группа 'Администратор' не найдена. Пожалуйста, сначала запустите 'flask seed-permissions'.")
                return
            
            admin_password = 'admin'
            
            admin = User(
                username='admin',
                password=admin_password, 
                group_id=admin_group.id,
                full_name='Администратор системы',
                position='Администратор'
            )
            db.session.add(admin)
            db.session.commit()
            print("Пользователь admin создан.")

    @app.cli.command("seed-permissions")
    def seed_permissions_command():
        """
        Создает и/или обновляет группы и права на основе словаря USER_GROUPS.
        Безопасна для повторного запуска.
        """
        from .models import Group, Permission
        from .utils import USER_GROUPS 

        with app.app_context():
            print("Синхронизация групп и прав...")
            
            group_objects = {}
            for group_key, group_info in USER_GROUPS.items():
                group_obj = Group.query.filter_by(name=group_info['name']).first()
                if not group_obj:
                    group_obj = Group(
                        name=group_info['name'],
                        is_deletable=group_info.get('is_deletable', True)
                    )
                    db.session.add(group_obj)
                else:
                    group_obj.is_deletable = group_info.get('is_deletable', True)
                group_objects[group_info['name']] = group_obj
            db.session.commit()
            print(f"Найдено/создано {len(group_objects)} групп.")

            all_permission_names = set()
            for group_info in USER_GROUPS.values():
                for perm in group_info['permissions']:
                    all_permission_names.add(perm)
            all_permission_names.add('manage_groups')

            permission_descriptions = {
                'view_logs': 'Просматривать журнал действий',
                'manage_users': 'Управлять пользователями',
                'manage_groups': 'Управлять группами и правами доступа',
                'view_organizations': 'Просматривать реестр организаций',
                'manage_organizations': 'Управлять реестром организаций',
                'view_map': 'Просматривать интерактивную карту',
                'view_profile': 'Просматривать личный кабинет',
                'manage_news': 'Управлять новостями',
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
                elif perm_obj.description != permission_descriptions.get(perm_name, 'Нет описания'):
                    perm_obj.description = permission_descriptions.get(perm_name, 'Нет описания')

                permission_objects[perm_name] = perm_obj
            db.session.commit()
            print(f"Найдено/создано/обновлено {len(permission_objects)} прав.")

            if 'admin' in USER_GROUPS and 'permissions' in USER_GROUPS['admin']:
                USER_GROUPS['admin']['permissions']['manage_groups'] = True
            
            for group_name, group_obj in group_objects.items():
                group_key = next((key for key, info in USER_GROUPS.items() if info['name'] == group_name), None)
                if group_key:
                    group_info = USER_GROUPS[group_key]
                    
                    group_obj.permissions.clear()
                    for perm_name, has_perm in group_info.get('permissions', {}).items():
                        if has_perm and perm_name in permission_objects:
                            group_obj.permissions.append(permission_objects[perm_name])
            
            db.session.commit()

            print("Поиск устаревших прав...")
            db_permissions = Permission.query.all()
            for perm in db_permissions:
                if perm.name not in all_permission_names:
                    print(f"  - Найдено устаревшее право: '{perm.name}'. Удаление...")
                    for group in perm.groups:
                        group.permissions.remove(perm)
                    db.session.commit()
                    db.session.delete(perm)
            db.session.commit()

            print("Синхронизация завершена.")

    return app
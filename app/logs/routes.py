# app/logs/routes.py
from flask import render_template, request # Убрал flash, redirect, url_for, если они не нужны здесь
from app.models import UserActivity
from app.utils import permission_required_manual
from . import logs_bp
from sqlalchemy import func # для func.date
from datetime import datetime # для преобразования дат

@logs_bp.route('/')
@permission_required_manual('view_logs')
def view_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 25 # Можно сделать меньше для отображения с деталями

    query = UserActivity.query

    # Получаем параметры фильтрации
    username_filter = request.args.get('username', type=str)
    action_filter = request.args.get('action', type=str)
    entity_type_filter = request.args.get('entity_type', type=str)
    entity_id_filter = request.args.get('entity_id', type=int) # ID сущности - число
    date_from_str = request.args.get('date_from', type=str)
    date_to_str = request.args.get('date_to', type=str)

    # Применяем фильтры
    if username_filter:
        query = query.filter(UserActivity.username.ilike(f"%{username_filter}%"))
    if action_filter:
        query = query.filter(UserActivity.action.ilike(f"%{action_filter}%"))
    if entity_type_filter:
        query = query.filter(UserActivity.entity_type.ilike(f"%{entity_type_filter}%"))
    if entity_id_filter is not None: # Проверяем на None, так как 0 - валидный ID
        query = query.filter(UserActivity.entity_id == entity_id_filter)
    
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            # Фильтруем по дате, отбрасывая время. Для этого используем func.date() на поле timestamp.
            query = query.filter(func.date(UserActivity.timestamp) >= date_from)
        except ValueError:
            # Можно добавить flash-сообщение об ошибке формата даты
            pass # Игнорируем неверный формат или выводим ошибку
            
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            query = query.filter(func.date(UserActivity.timestamp) <= date_to)
        except ValueError:
            pass

    logs_pagination = query.order_by(UserActivity.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('logs.html', logs=logs_pagination)
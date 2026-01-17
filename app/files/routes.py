# app/files/routes.py
import os
from flask import render_template, current_app, send_from_directory, abort, redirect, url_for, flash
from app.utils import permission_required_manual
from . import files_bp

@files_bp.route('/')
@files_bp.route('/<path:subpath>')
@permission_required_manual('view_files')
def manager(subpath=""):
    base_dir = os.path.join(current_app.static_folder, 'uploads')
    full_path = os.path.normpath(os.path.join(base_dir, subpath))
    if not full_path.startswith(base_dir):
        abort(403)

    if not os.path.exists(full_path):
        flash("Путь не найден", "warning")
        return redirect(url_for('files.manager'))

    items = []
    try:
        for entry in os.scandir(full_path):
            rel_path = os.path.relpath(entry.path, base_dir).replace("\\", "/")
            items.append({
                'name': entry.name,
                'is_dir': entry.is_dir(),
                'path': rel_path,
                'size': f"{os.path.getsize(entry.path) // 1024} KB" if entry.is_file() else "",
                'ext': entry.name.split('.')[-1].lower() if entry.is_file() else "folder"
            })
    except PermissionError:
        abort(403)

    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

    breadcrumbs = []
    parts = subpath.split('/') if subpath else []
    curr_path = ""
    for p in parts:
        if not p: continue
        curr_path = os.path.join(curr_path, p).replace("\\", "/")
        breadcrumbs.append((p, curr_path))

    return render_template('file_manager.html', items=items, breadcrumbs_list=breadcrumbs, current_path=subpath)
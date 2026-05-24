import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


def save_file(file_obj, subfolder='', allowed_ext=None):
    if allowed_ext is None:
        allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

    if not file_obj or file_obj.filename == '':
        return None

    filename = secure_filename(file_obj.filename)
    if not allowed_file(filename, allowed_ext):
        return None

    ext = filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    upload_root = current_app.config['UPLOAD_FOLDER']
    dest_dir = os.path.join(upload_root, subfolder) if subfolder else upload_root
    os.makedirs(dest_dir, exist_ok=True)

    full_path = os.path.join(dest_dir, unique_name)
    file_obj.save(full_path)

    relative = os.path.join('uploads', subfolder, unique_name).replace('\\', '/')
    return relative


def delete_file(relative_path):
    if not relative_path:
        return
    static_dir = os.path.join(current_app.root_path, 'static')
    full = os.path.join(static_dir, relative_path)
    if os.path.exists(full):
        os.remove(full)

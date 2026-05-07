"""File upload utilities — supports local storage and Cloudinary"""
import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", set())


def save_file(file_obj) -> str | None:
    """
    Save an uploaded file and return its URL/path.
    Uses Cloudinary if USE_CLOUDINARY=True, otherwise saves locally.
    Returns None if the file is invalid.
    """
    if not file_obj or file_obj.filename == "":
        return None
    if not allowed_file(file_obj.filename):
        return None

    if current_app.config.get("USE_CLOUDINARY"):
        return _upload_cloudinary(file_obj)
    return _upload_local(file_obj)


def _upload_local(file_obj) -> str:
    filename = secure_filename(file_obj.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, unique_name)
    file_obj.save(save_path)
    return f"/uploads/{unique_name}"


def _upload_cloudinary(file_obj) -> str:
    import cloudinary.uploader
    result = cloudinary.uploader.upload(
        file_obj,
        folder="sheEarn",
        resource_type="image",
    )
    return result.get("secure_url", "")

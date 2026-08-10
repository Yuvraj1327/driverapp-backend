"""
Receipt/file storage abstraction. Uploads to Supabase Storage when configured;
falls back to local disk storage (uploads/) otherwise, so the app is fully
functional in local/dev environments without a Supabase project.
"""
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class StorageError(Exception):
    pass


def _get_supabase_client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None
    try:
        from supabase import Client, create_client

        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as exc:  # pragma: no cover
        logger.warning("Supabase client could not be initialized: %s", exc)
        return None


async def upload_receipt(file: UploadFile, subfolder: str = "receipts") -> str:
    """
    Uploads a receipt file and returns a publicly-resolvable URL/path.
    Uses Supabase Storage if configured, otherwise stores locally under UPLOAD_DIR.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise StorageError(
            f"Unsupported file type '{file.content_type}'. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}"
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise StorageError("File exceeds maximum allowed size of 10MB")

    extension = Path(file.filename or "receipt").suffix or ".bin"
    object_name = f"{subfolder}/{uuid.uuid4().hex}{extension}"

    client = _get_supabase_client()
    if client is not None:
        try:
            client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
                object_name, contents, {"content-type": file.content_type}
            )
            public_url = client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).get_public_url(
                object_name
            )
            return public_url
        except Exception as exc:  # pragma: no cover
            logger.error("Supabase upload failed, falling back to local storage: %s", exc)

    # Local fallback
    upload_dir = Path(settings.UPLOAD_DIR) / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)
    local_path = upload_dir / Path(object_name).name
    local_path.write_bytes(contents)
    return f"/{settings.UPLOAD_DIR}/{subfolder}/{Path(object_name).name}"

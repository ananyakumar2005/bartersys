"""
app/storage.py — Supabase Storage helpers
Handles image compression (Pillow) and upload/delete via supabase-py SDK.
"""
import io
import os
import uuid

from PIL import Image
from supabase import create_client, Client

# ── Config ────────────────────────────────────────────────────────────────────
MAX_DIMENSION = 1200       # px — longest side after resize
JPEG_QUALITY  = 85         # JPEG compression quality (0-100)
MAX_IMAGES    = 5          # per listing

ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _client() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(url, key)


def _bucket() -> str:
    return os.environ.get("SUPABASE_BUCKET", "item-images")


# ── Image processing ──────────────────────────────────────────────────────────

def _compress(file_stream) -> bytes:
    """Open any image, resize to MAX_DIMENSION, convert to JPEG bytes."""
    img = Image.open(file_stream)
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()


# ── Public API ────────────────────────────────────────────────────────────────

def upload_item_image(file_stream, user_id: int, item_id: int) -> str:
    """
    Compress and upload one image to Supabase Storage.
    Returns the public URL string.
    Raises on any SDK / network error — caller should catch.
    """
    compressed = _compress(file_stream)
    filename   = f"{uuid.uuid4().hex}.jpg"
    path       = f"{user_id}/{item_id}/{filename}"

    sb = _client()
    sb.storage.from_(_bucket()).upload(
        path=path,
        file=compressed,
        file_options={"content-type": "image/jpeg", "upsert": "false"},
    )

    return sb.storage.from_(_bucket()).get_public_url(path)


def delete_item_images(public_urls: list) -> None:
    """
    Remove a list of images from Supabase Storage given their public URLs.
    Silently ignores paths that cannot be parsed.
    """
    if not public_urls:
        return

    bucket   = _bucket()
    # Public URL format:
    #   https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
    marker   = f"/storage/v1/object/public/{bucket}/"
    paths    = []
    for url in public_urls:
        if marker in url:
            paths.append(url.split(marker, 1)[1])

    if paths:
        _client().storage.from_(bucket).remove(paths)

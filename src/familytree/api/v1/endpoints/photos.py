"""Photo upload, retrieval and deletion endpoints."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PIL import Image

from familytree.api.deps import get_db_session
from familytree.infrastructure.db.models import Photo
from familytree.infrastructure.db.repositories.photo_repo import PhotoRepository
from familytree.schemas.photo import PhotoResponse, PhotoDeleteResponse

router = APIRouter(prefix="/api/v1/photos", tags=["photos"])

# Максимальные размеры для сжатия
MAX_WIDTH = 2000
MAX_HEIGHT = 2000
WEBP_QUALITY = 85
THUMB_SIZE = (150, 150)
SMALL_SIZE = (400, 400)


def _process_image(file_path: Path) -> tuple[int, int, bytes]:
    """Open image, resize to max dimensions, convert to WebP. Returns (width, height, webp_bytes)."""
    with Image.open(file_path) as img:
        # Convert to RGB if necessary (WebP doesn't support palette mode)
        if img.mode in ("P", "PA"):
            img = img.convert("RGBA")
        elif img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Resize to fit within MAX_WIDTH x MAX_HEIGHT
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)
        width, height = img.size

        # Save as WebP
        import io
        buffer = io.BytesIO()
        save_kwargs = {"format": "WebP", "quality": WEBP_QUALITY, "optimize": True}
        if img.mode == "RGBA":
            save_kwargs["mode"] = "RGBA"
        img.save(buffer, **save_kwargs)
        return width, height, buffer.getvalue()


def _save_variants(webp_bytes: bytes, original_filename: str, base_path: Path) -> dict[str, Path]:
    """Save original, small, and thumb variants. Returns dict with paths."""
    variants = {}

    # Original (sized to MAX)
    original_path = base_path / f"{uuid4().hex}.webp"
    original_path.write_bytes(webp_bytes)
    variants["original"] = original_path

    # Small (400x400)
    small_path = base_path / f"{uuid4().hex}_small.webp"
    with Image.open(original_path) as img:
        img.thumbnail(SMALL_SIZE, Image.LANCZOS)
        import io
        buffer = io.BytesIO()
        save_kwargs = {"format": "WebP", "quality": 80, "optimize": True}
        if img.mode == "RGBA":
            save_kwargs["mode"] = "RGBA"
        img.save(buffer, **save_kwargs)
        small_path.write_bytes(buffer.getvalue())
    variants["small"] = small_path

    # Thumbnail (150x150)
    thumb_path = base_path / f"{uuid4().hex}_thumb.webp"
    with Image.open(original_path) as img:
        img.thumbnail(THUMB_SIZE, Image.LANCZOS)
        import io
        buffer = io.BytesIO()
        save_kwargs = {"format": "WebP", "quality": 75, "optimize": True}
        if img.mode == "RGBA":
            save_kwargs["mode"] = "RGBA"
        img.save(buffer, **save_kwargs)
        thumb_path.write_bytes(buffer.getvalue())
    variants["thumb"] = thumb_path

    return variants


@router.post("/upload", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    person_id: int | None = Query(None, description="ID персоны для привязки"),
    db: Session = Depends(get_db_session),
):
    """Upload a photo and optionally attach to a person."""
    # Validate MIME type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    # Validate extension
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Save original file temporarily
    temp_path = PhotoRepository.UPLOAD_DIR / f"temp_{uuid4().hex}{ext}"
    content = await file.read()
    temp_path.write_bytes(content)

    try:
        # Process image
        width, height, webp_bytes = _process_image(temp_path)
        file_size = len(webp_bytes)

        # Create subdirectory for this person (or root)
        if person_id:
            person_dir = PhotoRepository.UPLOAD_DIR / "persons" / str(person_id)
        else:
            person_dir = PhotoRepository.UPLOAD_DIR / "unattached"
        person_dir.mkdir(parents=True, exist_ok=True)

        # Save variants
        variants = _save_variants(webp_bytes, file.filename, person_dir)

        # Get max sort_order for this person
        repo = PhotoRepository(db)
        existing = repo.get_by_person_id(person_id) if person_id else []
        max_order = max((p.sort_order for p in existing), default=-1)

        # Create DB record
        photo = Photo(
            person_id=person_id,
            filename=variants["original"].name,
            original_filename=file.filename,
            mime_type="image/webp",
            width=width,
            height=height,
            file_size=file_size,
            sort_order=max_order + 1,
        )
        repo.create(photo)
        db.commit()
        db.refresh(photo)

        return PhotoResponse.model_validate(photo)

    finally:
        # Clean up temporary file
        if temp_path.exists():
            temp_path.unlink()


@router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo(photo_id: int, db: Session = Depends(get_db_session)):
    """Get photo metadata."""
    repo = PhotoRepository(db)
    photo = repo.get_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return PhotoResponse.model_validate(photo)


@router.get("/{photo_id}/file")
def get_photo_file(photo_id: int, size: str = Query("original", pattern="^(original|small|thumb)$")):
    """Get photo file (original, small, or thumb)."""
    repo = PhotoRepository(None)  # We don't need DB for file access
    photo = PhotoRepository.__new__(PhotoRepository)
    photo.filename = None  # Placeholder

    # Find the file
    for root in [PhotoRepository.UPLOAD_DIR / "persons", PhotoRepository.UPLOAD_DIR / "unattached"]:
        if root.exists():
            for person_folder in root.iterdir():
                if person_folder.is_dir():
                    for variant_file in person_folder.glob(f"*_{size}.webp"):
                        if variant_file.exists():
                            return FileResponse(
                                path=variant_file,
                                media_type="image/webp",
                                filename=variant_file.name,
                            )

    raise HTTPException(status_code=404, detail="Photo file not found")


@router.delete("/{photo_id}", response_model=PhotoDeleteResponse)
def delete_photo(photo_id: int, db: Session = Depends(get_db_session)):
    """Delete a photo (file + DB record)."""
    repo = PhotoRepository(db)
    photo = repo.get_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Delete file variants
    for variant in ["original", "small", "thumb"]:
        repo.delete_file(photo.filename.replace(".webp", f"_{variant}.webp") if variant != "original" else photo.filename)

    repo.delete(photo)
    db.commit()

    return PhotoDeleteResponse(deleted=True, filename=photo.filename)


@router.get("/person/{person_id}", response_model=list[PhotoResponse])
def get_person_photos(person_id: int, db: Session = Depends(get_db_session)):
    """Get all photos for a person."""
    repo = PhotoRepository(db)
    photos = repo.get_by_person_id(person_id)
    return [PhotoResponse.model_validate(p) for p in photos]

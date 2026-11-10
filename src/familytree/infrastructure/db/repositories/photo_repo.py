"""Repository for Photo model."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from familytree.infrastructure.db.models import Photo


class PhotoRepository:
    """CRUD operations for Photo."""

    UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads" / "photos"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, photo_id: int) -> Photo | None:
        return self.session.get(Photo, photo_id)

    def get_by_person_id(self, person_id: int) -> list[Photo]:
        stmt = select(Photo).where(Photo.person_id == person_id).order_by(Photo.sort_order, Photo.id)
        return self.session.execute(stmt).scalars().all()

    def create(self, photo: Photo) -> Photo:
        self.session.add(photo)
        self.session.flush()
        return photo

    def update(self, photo: Photo, **kwargs) -> Photo:
        for key, value in kwargs.items():
            if hasattr(photo, key):
                setattr(photo, key, value)
        self.session.flush()
        return photo

    def delete(self, photo: Photo) -> bool:
        self.session.delete(photo)
        self.session.flush()
        return True

    def generate_filename(self, original_filename: str) -> tuple[str, str]:
        """Generate unique filename preserving extension."""
        ext = Path(original_filename).suffix.lower()
        filename = f"{uuid4().hex}{ext}"
        return filename, ext

    def save_file(self, upload_file: UploadFile, filename: str) -> Path:
        """Save uploaded file to disk."""
        file_path = self.UPLOAD_DIR / filename
        content = upload_file.file.read()
        file_path.write_bytes(content)
        return file_path

    def get_file_path(self, filename: str) -> Path:
        return self.UPLOAD_DIR / filename

    def file_exists(self, filename: str) -> bool:
        return self.get_file_path(filename).exists()

    def delete_file(self, filename: str) -> bool:
        file_path = self.get_file_path(filename)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

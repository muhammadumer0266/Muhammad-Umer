"""Validation and naming for admin-uploaded files (photos, resume, certificates).

Uploads are untrusted even when only the owner can make them: a stolen
admin session, or a file picked up from somewhere else, must not be able to
smuggle HTML/SVG/script content that later gets served from this origin.

Every upload is therefore:
- restricted to an explicit extension allowlist (no SVG, no HTML),
- size-capped,
- checked by content, not just name (PDF magic bytes; images are fully
  decoded by Pillow through ImageField / validate_image_content),
- stored under a random name, so the original filename (which may contain
  path tricks or personal info) never reaches the filesystem or URL.
"""

import uuid
from pathlib import PurePath

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
DOCUMENT_EXTENSIONS = ["pdf"]

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024

_PDF_MAGIC = b"%PDF-"


@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes

    def __call__(self, file) -> None:
        if file.size > self.max_bytes:
            limit_mb = self.max_bytes / (1024 * 1024)
            raise ValidationError(f"File too large (limit {limit_mb:g} MB).", code="file_too_large")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MaxFileSizeValidator) and other.max_bytes == self.max_bytes


def validate_pdf_content(file) -> None:
    """Rejects anything that isn't actually a PDF, whatever its extension says."""
    position = file.tell() if hasattr(file, "tell") else 0
    file.seek(0)
    header = file.read(len(_PDF_MAGIC))
    file.seek(position)
    if header != _PDF_MAGIC:
        raise ValidationError("This file is not a valid PDF.", code="invalid_pdf")


def validate_image_content(file) -> None:
    """Fully decodes an image so polyglot/truncated files are rejected.

    ImageField only calls Image.verify() on new uploads via its form field;
    this is used on plain FileFields that accept images or PDFs.
    """
    from PIL import Image

    position = file.tell() if hasattr(file, "tell") else 0
    file.seek(0)
    try:
        with Image.open(file) as img:
            if (img.format or "").lower() not in {"jpeg", "png", "webp"}:
                raise ValidationError("Unsupported image format.", code="invalid_image")
            img.verify()
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("This file is not a valid image.", code="invalid_image") from exc
    finally:
        file.seek(position)


def validate_image_or_pdf(file) -> None:
    extension = PurePath(file.name).suffix.lower().lstrip(".")
    if extension in DOCUMENT_EXTENSIONS:
        MaxFileSizeValidator(MAX_DOCUMENT_BYTES)(file)
        validate_pdf_content(file)
    else:
        MaxFileSizeValidator(MAX_IMAGE_BYTES)(file)
        validate_image_content(file)


image_validators = [
    FileExtensionValidator(IMAGE_EXTENSIONS),
    MaxFileSizeValidator(MAX_IMAGE_BYTES),
]
pdf_validators = [
    FileExtensionValidator(DOCUMENT_EXTENSIONS),
    MaxFileSizeValidator(MAX_DOCUMENT_BYTES),
    validate_pdf_content,
]
image_or_pdf_validators = [
    FileExtensionValidator(IMAGE_EXTENSIONS + DOCUMENT_EXTENSIONS),
    validate_image_or_pdf,
]


@deconstructible
class RandomFilename:
    """upload_to callable: keeps only the (lowercased) extension, randomizes the rest."""

    def __init__(self, folder: str) -> None:
        self.folder = folder.strip("/")

    def __call__(self, instance, filename: str) -> str:
        extension = PurePath(filename).suffix.lower()
        return f"{self.folder}/{uuid.uuid4().hex}{extension}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RandomFilename) and other.folder == self.folder


@deconstructible
class SeoFilename:
    """upload_to callable for photos that should rank in image search.

    Google uses the file name as a (weak) relevance signal, so instead of a
    bare UUID this produces e.g. ``photos/muhammad-umer-pycon-talk-3f9a1c.jpg``:
    owner's name + the photo's title, plus a short random suffix so names
    never collide and the original filename still never reaches disk.
    """

    def __init__(self, folder: str, title_field: str = "") -> None:
        self.folder = folder.strip("/")
        self.title_field = title_field

    def __call__(self, instance, filename: str) -> str:
        from django.utils.text import slugify

        from apps.portfolio.models import Profile

        extension = PurePath(filename).suffix.lower()
        parts = [slugify(Profile.get_solo().full_name)]
        if self.title_field:
            parts.append(slugify(getattr(instance, self.title_field, "") or "")[:60])
        stem = "-".join(p for p in parts if p) or "photo"
        return f"{self.folder}/{stem}-{uuid.uuid4().hex[:6]}{extension}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, SeoFilename)
            and other.folder == self.folder
            and other.title_field == self.title_field
        )

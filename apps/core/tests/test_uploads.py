import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.uploads import (
    MaxFileSizeValidator,
    RandomFilename,
    validate_image_or_pdf,
    validate_pdf_content,
)


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_real_pdf_passes():
    validate_pdf_content(SimpleUploadedFile("c.pdf", b"%PDF-1.7\n...", "application/pdf"))


def test_html_renamed_to_pdf_is_rejected():
    fake = SimpleUploadedFile("c.pdf", b"<html><script>alert(1)</script>", "application/pdf")

    with pytest.raises(ValidationError):
        validate_pdf_content(fake)


def test_image_or_pdf_accepts_real_png():
    validate_image_or_pdf(SimpleUploadedFile("badge.png", _png_bytes(), "image/png"))


def test_image_or_pdf_rejects_svg_disguised_as_png():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>'

    with pytest.raises(ValidationError):
        validate_image_or_pdf(SimpleUploadedFile("badge.png", svg, "image/png"))


def test_size_limit_enforced():
    with pytest.raises(ValidationError):
        MaxFileSizeValidator(10)(SimpleUploadedFile("a.pdf", b"x" * 11))


def test_random_filename_drops_original_name_and_path():
    name = RandomFilename("certifications/files")(None, "../../etc/My Passport Scan.PDF")

    assert name.startswith("certifications/files/")
    assert name.endswith(".pdf")
    assert "Passport" not in name
    assert ".." not in name

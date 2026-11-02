"""Decode validation complements signature checks before image persistence."""
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError


def verify_decodable_image(uploaded_file):
    position = uploaded_file.tell()
    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise ValidationError("Invalid or corrupt image content.") from exc
    finally:
        uploaded_file.seek(position)

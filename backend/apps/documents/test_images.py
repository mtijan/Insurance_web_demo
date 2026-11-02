"""Small valid synthetic images for multipart integration tests."""
from io import BytesIO

from PIL import Image


def jpeg_bytes():
    content = BytesIO()
    Image.new("RGB", (2, 2), "white").save(content, format="JPEG")
    return content.getvalue()

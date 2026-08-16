from io import BytesIO
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_WIDTH = 1200
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_uploaded_image(uploaded_file):
    if uploaded_file.size > MAX_IMAGE_SIZE:
        raise ValidationError("L'image ne doit pas dépasser 5 Mo.")

    try:
        image = Image.open(uploaded_file)
        image.verify()
        image_format = image.format
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValidationError(
            "Le fichier doit être une image JPEG, PNG ou WebP valide."
        ) from error
    finally:
        uploaded_file.seek(0)

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Seuls les formats JPEG, PNG et WebP sont acceptés.")
    return uploaded_file


def process_uploaded_image(uploaded_file, *, preserve_transparency=False):
    uploaded_file.seek(0)
    image = ImageOps.exif_transpose(Image.open(uploaded_file))
    image.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_WIDTH * 4), Image.Resampling.LANCZOS)

    has_transparency = image.mode in ("RGBA", "LA") and image.getchannel("A").getextrema()[0] < 255
    output = BytesIO()
    if preserve_transparency and has_transparency:
        image.save(output, format="PNG", optimize=True)
        extension = "png"
    else:
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(output, format="JPEG", quality=85, optimize=True)
        extension = "jpg"

    return ContentFile(output.getvalue(), name=f"{uuid4().hex}.{extension}")

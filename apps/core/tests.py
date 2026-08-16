from io import BytesIO
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from .images import process_uploaded_image, validate_uploaded_image
from .qrcode import generate_qr_png
from .whatsapp import build_whatsapp_url


def make_image_file(width=1600, height=800, image_format="PNG"):
    output = BytesIO()
    Image.new("RGB", (width, height), color="#f2b84b").save(
        output,
        format=image_format,
    )
    return SimpleUploadedFile(
        f"image.{image_format.lower()}",
        output.getvalue(),
        content_type=f"image/{image_format.lower()}",
    )


class ImagePipelineTests(SimpleTestCase):
    def test_rejects_non_image_content(self):
        upload = SimpleUploadedFile(
            "malware.jpg",
            b"not an image",
            content_type="image/jpeg",
        )
        with self.assertRaisesMessage(ValidationError, "JPEG, PNG ou WebP valide"):
            validate_uploaded_image(upload)

    def test_rejects_file_larger_than_five_megabytes(self):
        upload = SimpleUploadedFile(
            "large.jpg",
            b"0" * (5 * 1024 * 1024 + 1),
            content_type="image/jpeg",
        )
        with self.assertRaisesMessage(ValidationError, "5 Mo"):
            validate_uploaded_image(upload)

    def test_processed_product_image_is_jpeg_and_at_most_1200px(self):
        upload = make_image_file()
        validate_uploaded_image(upload)
        processed = process_uploaded_image(upload)
        image = Image.open(processed)

        self.assertEqual(image.format, "JPEG")
        self.assertLessEqual(image.width, 1200)


class WhatsAppTests(SimpleTestCase):
    def test_builds_encoded_default_and_product_urls(self):
        default_url = build_whatsapp_url("22997000000")
        product_url = build_whatsapp_url("+229 97 00 00 00", "Chemise bleue")

        self.assertEqual(urlparse(default_url).netloc, "wa.me")
        self.assertIn("vos produits", parse_qs(urlparse(default_url).query)["text"][0])
        self.assertIn("Chemise bleue", parse_qs(urlparse(product_url).query)["text"][0])

    def test_missing_or_invalid_number_returns_none(self):
        self.assertIsNone(build_whatsapp_url(""))
        self.assertIsNone(build_whatsapp_url("numéro-invalide"))


class QrCodeTests(SimpleTestCase):
    def test_generates_png(self):
        content = generate_qr_png("https://example.com/boutique/")
        self.assertTrue(content.startswith(b"\x89PNG\r\n\x1a\n"))

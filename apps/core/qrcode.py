from io import BytesIO

import qrcode


def generate_qr_png(url):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#12182b", back_color="white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()

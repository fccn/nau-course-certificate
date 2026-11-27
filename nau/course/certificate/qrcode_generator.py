"""
Generates the QR code (SVG) that links a printed certificate back to its
public verification page on the Open edX LMS.

It replaces the previous third-party ``qrcode.tec-it.com`` API, which was
rate limited when certificates were exported in bulk, see
https://github.com/fccn/nau-technical/issues/676 and
https://github.com/fccn/nau-technical/issues/884.

Only the certificate page of the LMS can be encoded: callers pass the
certificate path (``certificates/<id>``) and the QR target URL is built
server side, so the service can't be used as a generic QR code generator.
"""
import io
import re

import qrcode
import qrcode.image.svg

QRCODE_ROUTE_PREFIX = "/qrcode/"

_CERTIFICATE_PATH_RE = re.compile(r"certificates/[0-9a-f]{32}")
_COLOR_RE = re.compile(r"(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")
_DEFAULT_COLOR = "000000"


def is_valid_certificate_path(path: str) -> bool:
    return bool(_CERTIFICATE_PATH_RE.fullmatch(path))


def build_certificate_url(lms_url: str, path: str) -> str:
    """
    Build the public LMS URL of a certificate, the content of the QR code.

    Raises:
        ValueError: if ``path`` isn't a ``certificates/<32 hex chars>`` path.
    """
    if not is_valid_certificate_path(path):
        raise ValueError("Invalid certificate path: {!r}".format(path))
    return lms_url.rstrip("/") + "/" + path


def generate_qrcode_svg(data: str, color: str = None) -> bytes:
    """
    Generate a QR code as an SVG with a transparent background.

    The SVG has a single vector path, so it stays sharp at any print size.

    Args:
        data (str): The content to encode.
        color (str): Optional hex color (``rgb`` or ``rrggbb``, without ``#``)
            of the QR code modules, defaults to black.

    Raises:
        ValueError: if ``color`` isn't a valid hex color.
    """
    color = color or _DEFAULT_COLOR
    if not _COLOR_RE.fullmatch(color):
        raise ValueError("Invalid color: {!r}".format(color))

    class _ColoredSvgImage(qrcode.image.svg.SvgPathImage):
        QR_PATH_STYLE = {**qrcode.image.svg.SvgPathImage.QR_PATH_STYLE, "fill": "#" + color}

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        border=0,
        image_factory=_ColoredSvgImage,
    )
    qr.add_data(data)
    qr.make(fit=True)
    output = io.BytesIO()
    qr.make_image().save(output)
    return output.getvalue()


def generate_certificate_qrcode_svg(lms_url: str, path: str, color: str = None) -> bytes:
    """
    Generate the QR code (SVG) of the certificate at ``path`` of the LMS.

    Raises:
        ValueError: if ``path`` or ``color`` are invalid.
    """
    return generate_qrcode_svg(build_certificate_url(lms_url, path), color)

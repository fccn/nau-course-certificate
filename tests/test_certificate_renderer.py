"""
Integration tests for nau.course.certificate.certificate_renderer.

Unlike test_render_options.py (which only tests pure, browser-free helper
functions), these tests drive the actual Playwright/Chromium rendering
pipeline end-to-end -- render_pdf(), render_image() and (indirectly)
_measure_natural_size() -- against a small static HTML fixture
(tests/fixtures/sample_certificate.html) served over a `file://` URL, so no
LMS/network dependency is required.

They require a Chromium browser to be installed for Playwright (`python -m
playwright install chromium`), same as the "docker" CI job already does; the
"test" CI job installs it too (see .github/workflows/ci.yml).

Two fixtures are used:
- sample_certificate.html: minimal box+banner fixture for precise,
  easy-to-reason-about pixel-dimension assertions.
- mock_certificate.html: a closer structural approximation of the real NAU
  certificate template (fixed-size A4-landscape box, absolutely-positioned
  logo/course images, real print-media hiding rules copied from the real
  template) -- see that file's own docstring for details.

Image assertions decode actual pixel dimensions via Pillow (pinned explicitly
in requirements-test.txt).
"""
import io
import pathlib

import pytest
from PIL import Image

from nau.course.certificate.browser_manager import close_browser
from nau.course.certificate.certificate_renderer import render_image, render_pdf

_FIXTURE_URL = pathlib.Path(__file__).parent.joinpath(
    "fixtures", "sample_certificate.html"
).as_uri()

# The fixture's ".certificate" box is a fixed 800x400 CSS-pixel design; its
# ".banner" element (which must be hidden by print-media emulation) would add
# another 50px of height if it were not hidden. See sample_certificate.html.
_FIXTURE_WIDTH = 800
_FIXTURE_HEIGHT = 400

_NAU_FIXTURE_URL = pathlib.Path(__file__).parent.joinpath(
    "fixtures", "mock_certificate.html"
).as_uri()

# The NAU-like fixture's ".ednxt-certificate" box is a fixed A4-landscape
# design (29.7cm x 21cm), same as the real certificate template; at 96 CSS
# px/inch that's 1122.5x793.7 CSS pixels, which Chromium rounds to the pixel
# counts below. See mock_certificate.html.
_NAU_FIXTURE_WIDTH = 1123
_NAU_FIXTURE_HEIGHT = 794


@pytest.fixture(autouse=True)
def _close_browser_after_each_test():
    """
    Close the shared Chromium browser after every test so each test starts
    from a clean state and no browser process leaks past the test session.
    """
    yield
    close_browser()


class TestRenderPdf:
    def test_produces_a_valid_pdf(self):
        pdf_bytes = render_pdf(_FIXTURE_URL, {})

        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 1000


class TestRenderImage:
    def test_produces_a_valid_jpeg_by_default(self):
        image_bytes = render_image(_FIXTURE_URL, {})

        assert image_bytes.startswith(b"\xff\xd8\xff")

    def test_hides_the_print_only_banner_and_measures_natural_size(self):
        # No crop is requested, so the full natural size is captured. If
        # print-media emulation failed to hide ".banner", or natural-size
        # measurement was wrong, the resulting image would be taller than
        # the fixture's 800x400 ".certificate" box (450px instead of 400px).
        image_bytes = render_image(_FIXTURE_URL, {})

        image = Image.open(io.BytesIO(image_bytes))
        assert image.size == (_FIXTURE_WIDTH, _FIXTURE_HEIGHT)

    def test_respects_png_format_option(self):
        image_bytes = render_image(_FIXTURE_URL, {"format": "png"})

        assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        image = Image.open(io.BytesIO(image_bytes))
        assert image.size == (_FIXTURE_WIDTH, _FIXTURE_HEIGHT)

    def test_zoom_scales_output_resolution_without_changing_layout(self):
        # `zoom` is applied via Playwright's `device_scale_factor`, a pure
        # output-resolution multiplier: the CSS layout (and therefore the
        # natural size used for cropping) stays the same, but the resulting
        # pixel dimensions are multiplied by the zoom factor.
        image_bytes = render_image(_FIXTURE_URL, {"zoom": "2"})

        image = Image.open(io.BytesIO(image_bytes))
        assert image.size == (_FIXTURE_WIDTH * 2, _FIXTURE_HEIGHT * 2)

    def test_crop_produces_an_image_of_the_requested_final_size(self):
        image_bytes = render_image(
            _FIXTURE_URL, {"crop-x": "0", "crop-y": "0", "crop-w": "300", "crop-h": "150"}
        )

        image = Image.open(io.BytesIO(image_bytes))
        assert image.size == (300, 150)


class TestRenderPdfWithNauLikeFixture:
    def test_produces_a_valid_pdf(self):
        pdf_bytes = render_pdf(_NAU_FIXTURE_URL, {})

        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 1000


class TestRenderImageWithNauLikeFixture:
    def test_measures_the_fixed_a4_landscape_natural_size_and_hides_print_only_chrome(self):
        # mock_certificate.html exercises a layout much closer to the real
        # NAU template than sample_certificate.html's single box+banner: an
        # absolutely-positioned A4-landscape design with several images, plus
        # the same ".sr-only"/".wrapper-about" print-hiding rules the real
        # template uses. If natural-size measurement or print-media hiding
        # broke for this more realistic layout, the output would not match
        # the fixed A4-landscape size (e.g. because hidden screen-only
        # elements added extra height, or absolutely-positioned content
        # wasn't accounted for).
        image_bytes = render_image(_NAU_FIXTURE_URL, {})

        image = Image.open(io.BytesIO(image_bytes))
        assert image.size == (_NAU_FIXTURE_WIDTH, _NAU_FIXTURE_HEIGHT)

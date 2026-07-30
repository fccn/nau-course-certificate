"""
Unit tests for nau.course.certificate.render_options.

These functions are pure (no browser required), so they're tested directly
against the option dicts as they would be extracted from the
``pdfkit-*``/``imgkit-*`` HTML meta tags of the certificate template
(see nau_base_certificate.mako), plus the "natural size" values that would be
measured from a live page by
``nau.course.certificate.certificate_renderer._measure_natural_size``.
"""
from nau.course.certificate.render_options import (
    build_pdf_options,
    build_screenshot_options,
    build_screenshot_viewport,
    get_zoom_factor,
)


class TestGetZoomFactor:
    def test_returns_default_when_absent(self):
        assert get_zoom_factor({}) == 1.0

    def test_parses_float_value(self):
        assert get_zoom_factor({"zoom": "1.3"}) == 1.3

    def test_returns_default_on_invalid_value(self):
        assert get_zoom_factor({"zoom": "not-a-number"}) == 1.0


class TestBuildPdfOptions:
    def test_defaults_print_background_true(self):
        options = build_pdf_options({})
        assert options["print_background"] is True

    def test_maps_page_size_to_format(self):
        options = build_pdf_options({"page-size": "A4"})
        assert options["format"] == "A4"

    def test_maps_landscape_orientation(self):
        options = build_pdf_options({"orientation": "Landscape"})
        assert options["landscape"] is True

    def test_maps_portrait_orientation(self):
        options = build_pdf_options({"orientation": "Portrait"})
        assert options["landscape"] is False

    def test_orientation_is_coerced_to_string_before_comparing(self):
        # Defensive: some callers may pass non-string values through; this
        # must not raise, and non-"landscape" values should map to False.
        options = build_pdf_options({"orientation": 123})
        assert options["landscape"] is False

    def test_maps_margins(self):
        options = build_pdf_options({
            "margin-top": "0mm",
            "margin-bottom": "0mm",
            "margin-left": "0mm",
            "margin-right": "0mm",
        })
        assert options["margin"] == {
            "top": "0mm",
            "bottom": "0mm",
            "left": "0mm",
            "right": "0mm",
        }

    def test_omits_margin_key_when_no_margins_given(self):
        options = build_pdf_options({})
        assert "margin" not in options

    def test_ignores_disable_smart_shrinking(self):
        # No Playwright equivalent, must not raise and must not leak into kwargs.
        options = build_pdf_options({"disable-smart-shrinking": ""})
        assert "disable-smart-shrinking" not in options
        assert "disable_smart_shrinking" not in options

    def test_omits_scale_when_zoom_absent(self):
        options = build_pdf_options({})
        assert "scale" not in options

    def test_maps_zoom_to_scale(self):
        options = build_pdf_options({"zoom": "1.3"})
        assert options["scale"] == 1.3

    def test_matches_certificate_template_options(self):
        # Mirrors the options set in nau_base_certificate.mako.
        options = build_pdf_options({
            "page-size": "A4",
            "orientation": "Landscape",
            "margin-left": "0mm",
            "margin-right": "0mm",
            "margin-bottom": "0mm",
            "margin-top": "0mm",
            "disable-smart-shrinking": "",
        })
        assert options == {
            "print_background": True,
            "format": "A4",
            "landscape": True,
            "margin": {
                "top": "0mm",
                "bottom": "0mm",
                "left": "0mm",
                "right": "0mm",
            },
        }


class TestBuildScreenshotViewport:
    def test_defaults_to_natural_size_when_no_crop(self):
        viewport = build_screenshot_viewport({}, natural_width=1123.0, natural_height=794.0)
        assert viewport == {"width": 1123.0, "height": 794.0}

    def test_grows_to_fit_crop_extending_beyond_natural_size(self):
        viewport = build_screenshot_viewport(
            {"crop-h": "2000", "crop-w": "2000"}, natural_width=1123.0, natural_height=794.0
        )
        assert viewport == {"width": 2000.0, "height": 2000.0}

    def test_crop_within_natural_size_keeps_natural_viewport(self):
        # Mirrors the real certificate template: crop-h smaller than the
        # natural page height once un-zoomed, no crop-w at all.
        viewport = build_screenshot_viewport(
            {"crop-h": "1025", "zoom": "1.3"}, natural_width=1123.0, natural_height=794.0
        )
        assert viewport == {"width": 1123.0, "height": 794.0}

    def test_accounts_for_crop_origin(self):
        # crop-w is absent here, so its fallback (natural_width) is offset by
        # crop-x, growing the viewport so the whole clip region fits.
        viewport = build_screenshot_viewport(
            {"crop-h": "100", "crop-w": "100", "crop-x": "50", "crop-y": "50"},
            natural_width=200.0, natural_height=200.0,
        )
        assert viewport == {"width": 200.0, "height": 200.0}


class TestBuildScreenshotOptions:
    def test_defaults_to_jpeg_full_page(self):
        options = build_screenshot_options({}, natural_width=1123.0, natural_height=794.0)
        assert options["type"] == "jpeg"
        assert options["full_page"] is True
        assert "clip" not in options

    def test_maps_png_format(self):
        options = build_screenshot_options({"format": "png"}, natural_width=1123.0, natural_height=794.0)
        assert options["type"] == "png"

    def test_normalizes_jpg_alias_to_jpeg(self):
        options = build_screenshot_options({"format": "jpg"}, natural_width=1123.0, natural_height=794.0)
        assert options["type"] == "jpeg"

    def test_format_is_coerced_to_string_before_comparing(self):
        # Defensive: some callers may pass non-string values through; this
        # must not raise, and unrecognized values should fall back to jpeg.
        options = build_screenshot_options({"format": 123}, natural_width=1123.0, natural_height=794.0)
        assert options["type"] == "jpeg"

    def test_maps_quality_for_jpeg(self):
        options = build_screenshot_options(
            {"format": "jpeg", "quality": "80"}, natural_width=1123.0, natural_height=794.0
        )
        assert options["quality"] == 80

    def test_ignores_quality_for_png(self):
        options = build_screenshot_options(
            {"format": "png", "quality": "80"}, natural_width=1123.0, natural_height=794.0
        )
        assert "quality" not in options

    def test_maps_crop_h_to_clip_using_natural_width(self):
        options = build_screenshot_options({"crop-h": "1025"}, natural_width=1123.0, natural_height=794.0)
        assert options["clip"] == {"x": 0.0, "y": 0.0, "width": 1123.0, "height": 1025.0}
        assert "full_page" not in options

    def test_divides_crop_h_by_zoom_factor(self):
        # crop-h is a literal *final* (post-zoom) pixel height: with
        # device_scale_factor emulating zoom, the CSS-pixel clip height must
        # be divided by the zoom factor so Playwright's own scaling brings it
        # back up to the configured final size.
        options = build_screenshot_options(
            {"crop-h": "1025", "zoom": "1.3"}, natural_width=1123.0, natural_height=794.0
        )
        assert options["clip"]["height"] == 1025.0 / 1.3

    def test_uses_natural_width_undivided_when_crop_w_absent(self):
        # The natural width fallback is not a "final pixel" target, so it's
        # used as-is regardless of zoom.
        options = build_screenshot_options(
            {"crop-h": "1025", "zoom": "1.3"}, natural_width=1123.0, natural_height=794.0
        )
        assert options["clip"]["width"] == 1123.0

    def test_maps_crop_h_and_crop_w(self):
        options = build_screenshot_options(
            {"crop-h": "1025", "crop-w": "800"}, natural_width=1123.0, natural_height=794.0
        )
        assert options["clip"]["width"] == 800.0
        assert options["clip"]["height"] == 1025.0

    def test_divides_crop_w_by_zoom_factor_when_given(self):
        options = build_screenshot_options(
            {"crop-w": "800", "zoom": "2"}, natural_width=1123.0, natural_height=794.0
        )
        assert options["clip"]["width"] == 400.0

    def test_maps_crop_origin(self):
        options = build_screenshot_options(
            {"crop-h": "1025", "crop-x": "10", "crop-y": "20"}, natural_width=1123.0, natural_height=794.0
        )
        assert options["clip"]["x"] == 10.0
        assert options["clip"]["y"] == 20.0

    def test_matches_certificate_template_options(self):
        # Mirrors the options set in nau_base_certificate.mako.
        options = build_screenshot_options({
            "format": "jpeg",
            "crop-h": "1025",
            "zoom": "1.3",
        }, natural_width=1123.0, natural_height=794.0)
        assert options == {
            "type": "jpeg",
            "clip": {"x": 0.0, "y": 0.0, "width": 1123.0, "height": 1025.0 / 1.3},
        }

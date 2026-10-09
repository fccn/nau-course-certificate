"""
Pure functions that translate the wkhtmltopdf/wkhtmltoimage-style option dict
(extracted from ``pdfkit-*``/``imgkit-*`` HTML meta tags, see
:meth:`nau.course.certificate.course_certificate_to_pdf.CourseCertificateToBase.generate_options`)
into keyword arguments understood by Playwright's ``Page.pdf()`` and
``Page.screenshot()`` APIs.

These functions have no side effects and don't require a browser, so they can
be unit tested in isolation.
"""

# wkhtmltoimage/imgkit accept both "jpg" and "jpeg", Playwright only accepts "jpeg".
_IMAGE_FORMAT_ALIASES = {
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "png": "png",
}


def get_zoom_factor(options: dict) -> float:
    """
    Extract the ``zoom`` factor from an options dict (``pdfkit-zoom`` or
    ``imgkit-zoom`` meta tag). Defaults to 1.0 (no zoom) when absent or invalid.
    """
    zoom_value = options.get("zoom")
    if zoom_value is None:
        return 1.0
    try:
        return float(zoom_value)
    except (TypeError, ValueError):
        return 1.0


def build_pdf_options(options: dict) -> dict:
    """
    Translate a pdfkit-style option dict into kwargs for Playwright's
    ``Page.pdf()``.

    Supported source keys: ``page-size``, ``orientation``, ``margin-top``,
    ``margin-bottom``, ``margin-left``, ``margin-right``, ``zoom``.

    ``disable-smart-shrinking`` has no Playwright equivalent: Chromium's
    print-to-pdf doesn't shrink content to fit by default, so this option is
    intentionally ignored.

    ``zoom`` is mapped to Playwright's native ``scale`` option (kept out of
    the returned dict when zoom is 1.0/absent, matching ``Page.pdf()``'s own
    default).
    """
    pdf_kwargs = {"print_background": True}

    page_size = options.get("page-size")
    if page_size:
        pdf_kwargs["format"] = page_size

    orientation = options.get("orientation")
    if orientation:
        pdf_kwargs["landscape"] = str(orientation).strip().lower() == "landscape"

    margin = {}
    for side in ("top", "bottom", "left", "right"):
        margin_value = options.get("margin-" + side)
        if margin_value is not None:
            margin[side] = margin_value
    if margin:
        pdf_kwargs["margin"] = margin

    zoom_factor = get_zoom_factor(options)
    if zoom_factor != 1.0:
        pdf_kwargs["scale"] = zoom_factor

    return pdf_kwargs


def build_screenshot_viewport(options: dict, natural_width: float, natural_height: float) -> dict:
    """
    Compute the CSS-pixel viewport size Playwright needs so that the
    requested crop region (if any) is fully rendered without any scrolling
    being required (``Page.screenshot()``'s ``clip`` option only works
    reliably for content within the current viewport, unlike ``full_page``).

    ``natural_width``/``natural_height`` are the page's own unconstrained
    content size, as measured by
    :func:`nau.course.certificate.certificate_renderer._measure_natural_size`.
    When a crop is requested that is fully contained within the natural size
    (the common case), the natural size is used as-is. When a crop extends
    beyond it, the viewport is grown to fit.
    """
    zoom_factor = get_zoom_factor(options)
    crop_x = float(options.get("crop-x", 0))
    crop_y = float(options.get("crop-y", 0))
    crop_w = options.get("crop-w")
    crop_h = options.get("crop-h")

    clip_right = crop_x + (float(crop_w) / zoom_factor if crop_w is not None else natural_width)
    clip_bottom = crop_y + (float(crop_h) / zoom_factor if crop_h is not None else natural_height)

    return {
        "width": max(natural_width, clip_right),
        "height": max(natural_height, clip_bottom),
    }


def build_screenshot_options(options: dict, natural_width: float, natural_height: float) -> dict:
    """
    Translate an imgkit-style option dict into kwargs for Playwright's
    ``Page.screenshot()``.

    Supported source keys: ``format`` (jpeg/png), ``quality`` (jpeg only),
    ``crop-h``/``crop-w`` (clip height/width), ``crop-x``/``crop-y`` (clip
    origin, default 0).

    ``crop-h``/``crop-w`` are literal *final* (post-zoom) pixel dimensions,
    matching wkhtmltoimage's behaviour where ``zoom`` uniformly scales the
    whole rendered output, crop included. Since ``zoom`` is applied here via
    Playwright's ``device_scale_factor`` (a pure output-resolution
    multiplier that leaves CSS layout untouched, see
    :func:`nau.course.certificate.certificate_renderer.render_image`), any
    given ``crop-h``/``crop-w`` must be divided by the zoom factor to get the
    CSS-pixel clip size Playwright expects; ``device_scale_factor`` then
    scales the captured pixels back up to the configured final size.

    When ``crop-w``/``crop-h`` is missing, ``natural_width``/
    ``natural_height`` (the page's own unconstrained content size in CSS
    pixels) is used instead, un-divided: it is not a "final pixel" target,
    just "however wide/tall the page naturally is", and is scaled by
    ``device_scale_factor`` like the rest of the page.

    When neither ``crop-h`` nor ``crop-w`` is present the full scrollable
    page is captured (``full_page=True``), same behaviour as imgkit's default.
    """
    image_format = options.get("format", "jpeg")
    screenshot_kwargs = {
        "type": _IMAGE_FORMAT_ALIASES.get(str(image_format).strip().lower(), "jpeg"),
    }

    if screenshot_kwargs["type"] == "jpeg" and "quality" in options:
        try:
            screenshot_kwargs["quality"] = int(options["quality"])
        except (TypeError, ValueError):
            pass

    crop_h = options.get("crop-h")
    crop_w = options.get("crop-w")
    if crop_h is not None or crop_w is not None:
        zoom_factor = get_zoom_factor(options)
        width = float(crop_w) / zoom_factor if crop_w is not None else natural_width
        height = float(crop_h) / zoom_factor if crop_h is not None else natural_height
        screenshot_kwargs["clip"] = {
            "x": float(options.get("crop-x", 0)),
            "y": float(options.get("crop-y", 0)),
            "width": width,
            "height": height,
        }
    else:
        screenshot_kwargs["full_page"] = True

    return screenshot_kwargs

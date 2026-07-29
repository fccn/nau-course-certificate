"""
Renders a certificate URL to PDF or image bytes using Playwright/Chromium.

This module replaces the previous ``pdfkit``/``imgkit`` (wkhtmltopdf-based)
rendering, see https://github.com/fccn/nau-technical/issues/879.

The ``options`` dict accepted by :func:`render_pdf` and :func:`render_image`
follows the same shape produced by
``CourseCertificateToBase.generate_options()``: a merge of the
``custom-header`` list of ``(name, value)`` tuples (used for the LMS
authentication/force-html header and ``Accept-Language``) with the
``pdfkit-*``/``imgkit-*`` meta tag values (with the prefix already stripped).
The actual translation of those options into Playwright kwargs is done in
:mod:`nau.course.certificate.render_options`.
"""
import logging

from nau.course.certificate.browser_manager import get_browser, run_in_browser_thread
from nau.course.certificate.render_options import (
    build_pdf_options,
    build_screenshot_options,
    build_screenshot_viewport,
    get_zoom_factor,
)

logger = logging.getLogger(__name__)

# How long to wait for the page (and its sub-resources) to finish loading
# before rendering, in milliseconds.
_NAVIGATION_TIMEOUT_MS = 60000

# Viewport used for the initial navigation when rendering an image. It's
# deliberately narrower/shorter than any real certificate template so the
# page's true "natural" (unconstrained) content size can be measured from the
# resulting overflow, see :func:`_measure_natural_size`. It's resized to the
# actual required size (via ``Page.set_viewport_size()``) before the
# screenshot is taken.
_PROBE_VIEWPORT = {"width": 200, "height": 100}


def _extract_custom_headers(options: dict) -> dict:
    """
    Convert the ``custom-header`` list of ``(name, value)`` tuples (see
    ``CourseCertificateToBase.generate_options()``) into a plain dict suitable
    for ``BrowserContext.set_extra_http_headers()``.
    """
    return dict(options.get("custom-header", []))


def _measure_natural_size(page) -> tuple:
    """
    Measure the page's natural (unconstrained) content size in CSS pixels.

    wkhtmltoimage's default behaviour (when no explicit ``--width``/
    ``--height`` is given, as is the case for every real certificate
    template) is to auto-size the output image to the page's own content
    size rather than to any fixed browser-like viewport. Chromium/Playwright
    has no equivalent "auto width" mode: the page is always laid out against
    a fixed viewport, so a certificate template designed for a fixed print
    size (e.g. A4 landscape) ends up left-aligned inside whatever viewport is
    used, leaving unwanted whitespace if that viewport is wider than the
    design.

    To replicate wkhtmltoimage's behaviour, the page must first be navigated
    with a viewport narrower/shorter than any real certificate template (see
    :data:`_PROBE_VIEWPORT`), forcing the (fixed-size) certificate design to
    overflow it; the resulting ``scrollWidth``/``scrollHeight`` on the root
    element then reveals the content's true natural size, regardless of the
    probe viewport's own size.
    """
    size = page.evaluate(
        "() => ({width: document.documentElement.scrollWidth,"
        " height: document.documentElement.scrollHeight})"
    )
    return float(size["width"]), float(size["height"])


def _render(url: str, headers: dict, render_fn, viewport=None, device_scale_factor=None):
    """
    Open a new isolated browser context/page navigated to ``url`` with the
    given extra HTTP ``headers``, call ``render_fn(page)`` to produce the
    output bytes, and make sure the context is always closed afterwards.

    The page's CSS media type is emulated as ``print`` before rendering,
    matching wkhtmltopdf/wkhtmltoimage's behaviour: the certificate template's
    ``@media print`` rules (see ``lms/static/certificates/sass/_print.scss``
    in edx-platform) hide the "you earned a certificate" banner and other
    chrome that should not appear in the generated PDF/image, only the
    certificate itself.

    Runs on the single dedicated browser thread (see
    ``browser_manager.run_in_browser_thread``), since Playwright's sync API
    objects can only be used from the OS thread that created them.
    """
    return run_in_browser_thread(
        _render_on_browser_thread, url, headers, render_fn, viewport, device_scale_factor
    )


def _render_on_browser_thread(url, headers, render_fn, viewport, device_scale_factor):
    browser = get_browser()
    context_kwargs = {"extra_http_headers": headers}
    if viewport is not None:
        context_kwargs["viewport"] = viewport
    if device_scale_factor is not None:
        context_kwargs["device_scale_factor"] = device_scale_factor
    context = browser.new_context(**context_kwargs)
    try:
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=_NAVIGATION_TIMEOUT_MS)
        page.emulate_media(media="print")
        return render_fn(page)
    finally:
        context.close()


def render_pdf(url: str, options: dict) -> bytes:
    """
    Render the given URL to a PDF byte array.

    Args:
        url (str): The certificate page URL to render.
        options (dict): Merged ``custom-header`` + ``pdfkit-*`` options, as
            produced by ``CourseCertificateToBase.generate_options()``.

    Returns:
        bytes: The rendered PDF file content.
    """
    logger.info("Rendering PDF with Playwright for URL: {}".format(url))
    headers = _extract_custom_headers(options)
    pdf_options = build_pdf_options(options)

    return _render(url, headers, lambda page: page.pdf(**pdf_options))


def render_image(url: str, options: dict) -> bytes:
    """
    Render the given URL to an image byte array (PNG or JPEG).

    Args:
        url (str): The certificate page URL to render.
        options (dict): Merged ``custom-header`` + ``imgkit-*`` options, as
            produced by ``CourseCertificateToBase.generate_options()``.

    Returns:
        bytes: The rendered image file content.
    """
    logger.info("Rendering image with Playwright for URL: {}".format(url))
    headers = _extract_custom_headers(options)
    zoom_factor = get_zoom_factor(options)

    def _do_render(page):
        # Replicate wkhtmltoimage's auto-width/height behaviour: measure the
        # page's real content size, then resize the viewport to it (instead
        # of rendering into an arbitrary fixed-size viewport, which would
        # leave whitespace around/clip a fixed-size certificate design).
        natural_width, natural_height = _measure_natural_size(page)
        viewport = build_screenshot_viewport(options, natural_width, natural_height)
        page.set_viewport_size({
            "width": round(viewport["width"]),
            "height": round(viewport["height"]),
        })
        screenshot_options = build_screenshot_options(options, natural_width, natural_height)
        return page.screenshot(**screenshot_options)

    # `zoom` is emulated with Playwright's native `device_scale_factor`: a
    # pure output-resolution multiplier that leaves CSS layout untouched
    # (unlike injecting a CSS `zoom` style, which was found to distort the
    # page's layout/overflow instead of just increasing output resolution).
    return _render(
        url,
        headers,
        _do_render,
        viewport=_PROBE_VIEWPORT,
        device_scale_factor=zoom_factor if zoom_factor and zoom_factor != 1.0 else None,
    )

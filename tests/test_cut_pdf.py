"""
Unit tests for nau.course.certificate.cut_pdf.

Test PDFs are generated on the fly with PyPDF2 (already a direct dependency)
rather than checked-in binary fixtures, so page counts are explicit/obvious
from the test code itself.
"""
import io

import PyPDF2
import pytest

from nau.course.certificate.cut_pdf import cut_pdf_limit_pages


def _make_pdf(num_pages: int) -> bytes:
    writer = PyPDF2.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _page_count(pdf_bytes: bytes) -> int:
    return len(PyPDF2.PdfReader(io.BytesIO(pdf_bytes)).pages)


class TestCutPdfLimitPages:
    def test_returns_the_same_pdf_unchanged_when_range_covers_all_pages(self):
        pdf = _make_pdf(3)

        result = cut_pdf_limit_pages(pdf, 0, 3)

        # Same object/bytes returned, not just an equivalent re-written copy.
        assert result is pdf

    def test_returns_none_when_start_is_beyond_the_last_page(self):
        pdf = _make_pdf(3)

        result = cut_pdf_limit_pages(pdf, 5, 10)

        assert result is None

    def test_clamps_end_when_it_exceeds_the_page_count(self):
        pdf = _make_pdf(3)

        result = cut_pdf_limit_pages(pdf, 0, 10)

        assert _page_count(result) == 3

    def test_produces_a_slice_with_the_requested_page_count(self):
        pdf = _make_pdf(5)

        result = cut_pdf_limit_pages(pdf, 1, 3)

        assert _page_count(result) == 2

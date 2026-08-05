"""
Unit tests for nau.course.certificate.digital_sign_pdf.

The signature-box/config-value/image-path logic is exercised through the
public digital_sign_pdf() function (its helpers are private closures, not
importable directly): endesive's real cms.sign() is mocked out so tests can
assert on the exact `dct` it was called with, while the certificate/private
key loading itself is left real (fast, offline, uses the repo's own dev
certificate at digital_signature_dev/, matching what config.sample.yml
documents for local development).

A dedicated end-to-end test (without mocking cms.sign) verifies actual PDF
signing works against that same dev certificate.
"""
import io
from unittest.mock import patch

import PyPDF2
import pytest

import nau.course.certificate.digital_sign_pdf as digital_sign_pdf_module
from nau.course.certificate.digital_sign_pdf import digital_sign_pdf

_DEV_P12_CONFIG = {
    "CERTIFICATE_P12_PATH": "./digital_signature_dev/sign-pdf.dev.nau.fccn.pt.p12",
    "CERTIFICATE_P12_PASSWORD": "1234",
}


def _make_pdf() -> bytes:
    writer = PyPDF2.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _sign_and_capture_dct(config: dict, language: str = "en") -> dict:
    """
    Call digital_sign_pdf() with cms.sign() mocked out, and return the `dct`
    dict it was invoked with (the second positional argument), so tests can
    assert on the signaturebox/contact/location/reason values that were
    actually computed, without needing to decode a real PDF signature.
    """
    with patch.object(digital_sign_pdf_module.cms, "sign", return_value=b"") as mock_sign:
        digital_sign_pdf(_make_pdf(), config, language)

    return mock_sign.call_args[0][1]


class TestSignatureBox:
    def test_parses_a_comma_separated_string_into_a_tuple_of_ints(self):
        config = {**_DEV_P12_CONFIG, "signaturebox": "10,20,30,40"}

        dct = _sign_and_capture_dct(config)

        assert dct["signaturebox"] == (10, 20, 30, 40)

    def test_defaults_when_signaturebox_is_absent(self):
        dct = _sign_and_capture_dct(dict(_DEV_P12_CONFIG))

        assert dct["signaturebox"] == (50, 50, 100, 100)


class TestGetConfigValue:
    def test_a_plain_string_value_is_used_regardless_of_language(self):
        config = {**_DEV_P12_CONFIG, "contact": "same@example.com"}

        dct = _sign_and_capture_dct(config, language="pt-pt")

        assert dct["contact"] == "same@example.com"

    def test_a_dict_value_selects_the_entry_for_the_given_language(self):
        config = {**_DEV_P12_CONFIG, "reason": {"pt-pt": "motivo", "en": "reason"}}

        dct_pt = _sign_and_capture_dct(config, language="pt-pt")
        dct_en = _sign_and_capture_dct(config, language="en")

        assert dct_pt["reason"] == "motivo"
        assert dct_en["reason"] == "reason"

    def test_falls_back_to_the_default_and_warns_when_language_is_missing(self, caplog):
        config = {**_DEV_P12_CONFIG, "location": {"en": "London"}}

        with caplog.at_level("WARNING"):
            dct = _sign_and_capture_dct(config, language="pt-pt")

        assert dct["location"] == "Some city"
        assert any(
            "Incorrect configuration" in record.message for record in caplog.records
        )


class TestSignatureImagePath:
    def test_uses_the_image_for_the_given_language_when_it_exists(self):
        dct = _sign_and_capture_dct(dict(_DEV_P12_CONFIG), language="pt-pt")

        assert dct["signature_img"] == "./static/images/digital_sign/digital_signature_pt-pt.png"

    def test_falls_back_to_the_english_image_when_the_language_has_none(self):
        dct = _sign_and_capture_dct(dict(_DEV_P12_CONFIG), language="fr")

        assert dct["signature_img"] == "./static/images/digital_sign/digital_signature_en.png"

    def test_falls_back_to_the_english_image_when_no_language_is_given(self):
        dct = _sign_and_capture_dct(dict(_DEV_P12_CONFIG), language=None)

        assert dct["signature_img"] == "./static/images/digital_sign/digital_signature_en.png"


class TestDigitalSignPdfEndToEnd:
    def test_signs_a_real_pdf_with_the_dev_certificate(self):
        # No mocking here: exercises the real endesive/cryptography signing
        # path end-to-end (offline, using the repo's own dev .p12), matching
        # what config.sample.yml documents for local development.
        pdf_bytes = _make_pdf()

        signed_pdf = digital_sign_pdf(pdf_bytes, dict(_DEV_P12_CONFIG), "en")

        assert signed_pdf.startswith(b"%PDF-")
        # The signature is appended after the original PDF content.
        assert len(signed_pdf) > len(pdf_bytes)

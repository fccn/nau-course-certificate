"""
Unit tests for nau.course.certificate.qrcode_generator.
"""
import pytest

from nau.course.certificate.qrcode_generator import (
    build_certificate_url,
    generate_certificate_qrcode_svg,
    generate_qrcode_svg,
    is_valid_certificate_path,
)

_CERTIFICATE_ID = "4d1d8ad2bcea43b7bac918ca328183b9"


class TestIsValidCertificatePath:
    def test_accepts_a_certificate_path(self):
        assert is_valid_certificate_path("certificates/" + _CERTIFICATE_ID)

    @pytest.mark.parametrize(
        "path",
        [
            "",
            "certificates/",
            "certificates/abc123",
            "certificates/" + _CERTIFICATE_ID.upper(),
            "certificates/" + _CERTIFICATE_ID + "/",
            "certificates/" + _CERTIFICATE_ID + "\n",
            "certificates/" + _CERTIFICATE_ID + "/extra",
            "../certificates/" + _CERTIFICATE_ID,
            "admin/" + _CERTIFICATE_ID,
            "https://evil.example/certificates/" + _CERTIFICATE_ID,
        ],
    )
    def test_rejects_anything_else(self, path):
        assert not is_valid_certificate_path(path)


class TestBuildCertificateUrl:
    def test_joins_the_lms_url_and_the_certificate_path(self):
        assert (
            build_certificate_url("https://lms.nau.edu.pt", "certificates/" + _CERTIFICATE_ID)
            == "https://lms.nau.edu.pt/certificates/" + _CERTIFICATE_ID
        )

    def test_does_not_duplicate_the_slash_of_the_lms_url(self):
        assert (
            build_certificate_url("https://lms.nau.edu.pt/", "certificates/" + _CERTIFICATE_ID)
            == "https://lms.nau.edu.pt/certificates/" + _CERTIFICATE_ID
        )

    def test_raises_for_an_invalid_path(self):
        with pytest.raises(ValueError):
            build_certificate_url("https://lms.nau.edu.pt", "admin/")


class TestGenerateQrcodeSvg:
    def test_generates_an_svg_with_a_single_black_path_by_default(self):
        svg = generate_qrcode_svg("https://lms.nau.edu.pt/certificates/" + _CERTIFICATE_ID)

        assert svg.startswith(b"<?xml") or svg.startswith(b"<svg")
        assert b"<svg" in svg
        assert svg.count(b"<path") == 1
        assert b'fill="#000000"' in svg

    def test_uses_the_requested_color(self):
        svg = generate_qrcode_svg("data", color="ffffff")

        assert b'fill="#ffffff"' in svg

    def test_is_deterministic(self):
        assert generate_qrcode_svg("data") == generate_qrcode_svg("data")

    def test_does_not_leak_the_color_to_following_calls(self):
        generate_qrcode_svg("data", color="ff0000")

        assert b'fill="#000000"' in generate_qrcode_svg("data")

    @pytest.mark.parametrize("color", ["#fff", "red", "ff", "fffff", "ffffffff", '"><script>', "gg0000", "ffffff\n"])
    def test_rejects_an_invalid_color(self, color):
        with pytest.raises(ValueError):
            generate_qrcode_svg("data", color=color)


class TestGenerateCertificateQrcodeSvg:
    def test_encodes_the_certificate_url(self):
        expected = generate_qrcode_svg("https://lms.nau.edu.pt/certificates/" + _CERTIFICATE_ID, "ffffff")

        assert (
            generate_certificate_qrcode_svg("https://lms.nau.edu.pt", "certificates/" + _CERTIFICATE_ID, "ffffff")
            == expected
        )

    def test_raises_for_an_invalid_path(self):
        with pytest.raises(ValueError):
            generate_certificate_qrcode_svg("https://lms.nau.edu.pt", "certificates/not-a-valid-id")

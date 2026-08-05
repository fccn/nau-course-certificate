"""
Unit tests for nau.course.certificate.course_certificate_to_pdf.

`config` here is a plain dict, matching what app.py's read_config() actually
passes in (Configuration(...).config(), i.e. the raw parsed YAML, not the
Configuration object itself).

requests.get (used to fetch the certificate HTML/meta tags), boto3.client
(S3 caching), render_pdf/render_image (Playwright rendering, tested
separately in test_certificate_renderer.py), cut_pdf_limit_pages and
digital_sign_pdf are all mocked so these tests exercise only
CourseCertificateToBase/CourseCertificateToPDF/CourseCertificateToImage's own
option-extraction, caching and dispatch logic.
"""
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from nau.course.certificate.course_certificate_to_pdf import (
    CourseCertificateToImage,
    CourseCertificateToPDF,
)

_BASE_CONFIG = {"LMS_SERVER_URL": "http://lms.example.test"}

_BUCKET_CONFIG = {
    **_BASE_CONFIG,
    "BUCKET_NAME": "test-bucket",
    "BUCKET_AWS_ACCESS_KEY_ID": "AKIAEXAMPLE",
    "BUCKET_AWS_SECRET_ACCESS_KEY": "secret",
}


def _html_with_metas(metas: dict) -> str:
    meta_tags = "\n".join(
        '<meta name="{}" content="{}">'.format(name, content)
        for name, content in metas.items()
    )
    return "<html><head>{}</head><body></body></html>".format(meta_tags)


def _mock_requests_get(metas: dict = None):
    mock_response = MagicMock()
    mock_response.text = _html_with_metas(metas or {})
    return patch(
        "nau.course.certificate.course_certificate_to_pdf.requests.get",
        return_value=mock_response,
    )


def _make_certificate_to_pdf(
    config: dict = None, metas: dict = None, path: str = "certificates/abc123", query_string: bytes = b""
) -> CourseCertificateToPDF:
    with _mock_requests_get(metas):
        return CourseCertificateToPDF(config if config is not None else dict(_BASE_CONFIG), path, query_string)


def _make_certificate_to_image(
    config: dict = None, metas: dict = None, path: str = "certificates/abc123", query_string: bytes = b""
) -> CourseCertificateToImage:
    with _mock_requests_get(metas):
        return CourseCertificateToImage(config if config is not None else dict(_BASE_CONFIG), path, query_string)


class TestLmsServerUrlConfiguration:
    def test_raises_when_neither_lms_server_url_nor_openedx_lms_url_are_configured(self, monkeypatch):
        monkeypatch.delenv("OPENEDX_LMS_URL", raising=False)

        with _mock_requests_get(), pytest.raises(Exception, match="Bad configuration"):
            CourseCertificateToPDF({}, "certificates/abc123", b"")

    def test_openedx_lms_url_config_key_is_accepted_as_a_fallback(self):
        config = {"OPENEDX_LMS_URL": "http://lms.example.test"}

        cert = _make_certificate_to_pdf(config=config)

        assert cert._url == "http://lms.example.test/certificates/abc123"

    def test_openedx_lms_url_environment_variable_is_accepted_as_a_last_resort(self, monkeypatch):
        monkeypatch.setenv("OPENEDX_LMS_URL", "http://lms.example.test")

        cert = _make_certificate_to_pdf(config={})

        assert cert._url == "http://lms.example.test/certificates/abc123"


class TestGenerateOptions:
    def test_extracts_and_strips_the_prefix_from_matching_meta_tags(self):
        cert = _make_certificate_to_pdf(
            metas={"pdfkit-page-size": "A4", "pdfkit-orientation": "Landscape", "unrelated-meta": "ignored"}
        )

        options = cert.generate_options("pdfkit-")

        assert options["page-size"] == "A4"
        assert options["orientation"] == "Landscape"
        assert "unrelated-meta" not in options

    def test_merges_in_the_force_html_custom_header(self):
        cert = _make_certificate_to_pdf()

        options = cert.generate_options("pdfkit-")

        assert options["custom-header"] == [("X-NAU-Certificate-force-html", "True")]

    def test_adds_accept_language_header_when_language_query_param_is_present(self):
        cert = _make_certificate_to_pdf(query_string=b"language=pt-pt")

        options = cert.generate_options("pdfkit-")

        assert ("Accept-Language", "pt-pt") in options["custom-header"]

    def test_no_accept_language_header_when_language_query_param_is_absent(self):
        cert = _make_certificate_to_pdf(query_string=b"")

        options = cert.generate_options("pdfkit-")

        assert all(name != "Accept-Language" for name, _ in options["custom-header"])


class TestCacheToBucket:
    def test_false_when_no_bucket_credentials_are_configured(self):
        cert = _make_certificate_to_pdf(config=dict(_BASE_CONFIG))

        assert not cert.cache_to_bucket()

    def test_false_when_bucket_name_is_missing(self):
        config = {**_BASE_CONFIG, "BUCKET_AWS_ACCESS_KEY_ID": "x", "BUCKET_AWS_SECRET_ACCESS_KEY": "y"}

        cert = _make_certificate_to_pdf(config=config)

        assert not cert.cache_to_bucket()

    def test_true_when_all_bucket_credentials_are_configured(self):
        cert = _make_certificate_to_pdf(config=dict(_BUCKET_CONFIG))

        assert cert.cache_to_bucket()


class TestConvertS3Caching:
    def test_cache_hit_returns_the_cached_certificate_without_rendering(self):
        cert = _make_certificate_to_pdf(config=dict(_BUCKET_CONFIG))

        with patch.object(
            CourseCertificateToPDF, "get_certificate_on_s3_bucket", return_value=b"cached-pdf-bytes"
        ) as mock_get, patch(
            "nau.course.certificate.course_certificate_to_pdf.render_pdf"
        ) as mock_render, patch.object(
            CourseCertificateToPDF, "save_certificate"
        ) as mock_save:
            result = cert.convert()

        assert result == b"cached-pdf-bytes"
        mock_get.assert_called_once()
        mock_render.assert_not_called()
        # Note: convert() unconditionally re-saves whatever binary_output
        # ends up being (cached or freshly rendered) whenever caching is
        # enabled, so a cache hit still triggers a (redundant) save call --
        # this is existing/current behaviour, not something this test suite
        # changes.
        mock_save.assert_called_once()

    def test_cache_miss_renders_and_saves_the_new_certificate(self):
        cert = _make_certificate_to_pdf(config=dict(_BUCKET_CONFIG))

        with patch.object(
            CourseCertificateToPDF, "get_certificate_on_s3_bucket", return_value=None
        ) as mock_get, patch(
            "nau.course.certificate.course_certificate_to_pdf.render_pdf", return_value=b"rendered-pdf-bytes"
        ) as mock_render, patch.object(
            CourseCertificateToPDF, "save_certificate"
        ) as mock_save:
            result = cert.convert()

        assert result == b"rendered-pdf-bytes"
        mock_get.assert_called_once()
        mock_render.assert_called_once()
        mock_save.assert_called_once()

    def test_no_caching_attempted_when_bucket_is_not_configured(self):
        cert = _make_certificate_to_pdf(config=dict(_BASE_CONFIG))

        with patch.object(CourseCertificateToPDF, "get_certificate_on_s3_bucket") as mock_get, patch(
            "nau.course.certificate.course_certificate_to_pdf.render_pdf", return_value=b"rendered-pdf-bytes"
        ) as mock_render:
            result = cert.convert()

        assert result == b"rendered-pdf-bytes"
        mock_get.assert_not_called()
        mock_render.assert_called_once()

    def test_certificate_version_meta_changes_the_cache_key(self):
        cert = _make_certificate_to_pdf(
            config=dict(_BUCKET_CONFIG),
            metas={"nau-course-certificate-version": "v2 with spaces"},
        )

        with patch.object(
            CourseCertificateToPDF, "get_certificate_on_s3_bucket", return_value=b"cached"
        ) as mock_get, patch.object(CourseCertificateToPDF, "save_certificate"):
            cert.convert()

        s3_key = mock_get.call_args[0][-1]
        assert s3_key == "certificates/abc123/v2_with_spaces.pdf"

    def test_uses_the_no_version_key_when_no_version_meta_is_present(self):
        cert = _make_certificate_to_pdf(config=dict(_BUCKET_CONFIG))

        with patch.object(
            CourseCertificateToPDF, "get_certificate_on_s3_bucket", return_value=b"cached"
        ) as mock_get, patch.object(CourseCertificateToPDF, "save_certificate"):
            cert.convert()

        s3_key = mock_get.call_args[0][-1]
        assert s3_key == "certificates/abc123/no-version.pdf"


class TestGetCertificateOnS3Bucket:
    def test_returns_none_when_the_key_does_not_exist(self):
        mock_s3_client = MagicMock()
        mock_s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "not found"}}, "GetObject"
        )

        with patch("nau.course.certificate.course_certificate_to_pdf.boto3.client", return_value=mock_s3_client):
            result = CourseCertificateToPDF.get_certificate_on_s3_bucket(
                "bucket", "http://s3.example.test", "key", "secret", "certificates/abc123/no-version.pdf"
            )

        assert result is None

    def test_returns_the_object_content_when_found(self):
        mock_body = MagicMock()
        mock_body.read.return_value = b"the-certificate-bytes"
        mock_s3_client = MagicMock()
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        with patch("nau.course.certificate.course_certificate_to_pdf.boto3.client", return_value=mock_s3_client):
            result = CourseCertificateToPDF.get_certificate_on_s3_bucket(
                "bucket", "http://s3.example.test", "key", "secret", "certificates/abc123/no-version.pdf"
            )

        assert result == b"the-certificate-bytes"


class TestLoadCertificateHttpMetas:
    def test_sends_the_force_html_header(self):
        mock_response = MagicMock(text="<html></html>")
        with patch(
            "nau.course.certificate.course_certificate_to_pdf.requests.get", return_value=mock_response
        ) as mock_get:
            CourseCertificateToPDF.load_certificate_http_metas(
                "http://lms.example.test/certificates/abc123",
                "X-NAU-Certificate-force-html",
                "True",
                None,
                None,
            )

        mock_get.assert_called_once_with(
            "http://lms.example.test/certificates/abc123",
            headers={"X-NAU-Certificate-force-html": "True"},
            auth=None,
        )

    def test_no_auth_when_only_one_of_user_or_pass_is_configured(self):
        mock_response = MagicMock(text="<html></html>")
        with patch(
            "nau.course.certificate.course_certificate_to_pdf.requests.get", return_value=mock_response
        ) as mock_get:
            CourseCertificateToPDF.load_certificate_http_metas(
                "http://lms.example.test/certificates/abc123", "X", "True", "user-only", None
            )

        assert mock_get.call_args.kwargs["auth"] is None

    def test_http_basic_auth_applied_when_both_user_and_pass_are_configured(self):
        mock_response = MagicMock(text="<html></html>")
        with patch(
            "nau.course.certificate.course_certificate_to_pdf.requests.get", return_value=mock_response
        ) as mock_get:
            CourseCertificateToPDF.load_certificate_http_metas(
                "http://lms.example.test/certificates/abc123", "X", "True", "the-user", "the-pass"
            )

        auth = mock_get.call_args.kwargs["auth"]
        assert auth is not None
        assert (auth.username, auth.password) == ("the-user", "the-pass")


class TestDigitalSignaturePassthrough:
    def test_digital_sign_pdf_is_invoked_with_the_requested_language_when_configured(self):
        cert = _make_certificate_to_pdf(
            config={**_BASE_CONFIG, "DIGITAL_SIGNATURE": {"CERTIFICATE_P12_PATH": "x"}},
            query_string=b"language=pt-pt",
        )

        with patch(
            "nau.course.certificate.course_certificate_to_pdf.render_pdf", return_value=b"pdf-bytes"
        ), patch(
            "nau.course.certificate.course_certificate_to_pdf.digital_sign_pdf", return_value=b"signed-pdf-bytes"
        ) as mock_sign:
            result = cert.generate_new_certificate_to_dest_format()

        assert result == b"signed-pdf-bytes"
        mock_sign.assert_called_once_with(b"pdf-bytes", {"CERTIFICATE_P12_PATH": "x"}, "pt-pt")

    def test_digital_sign_pdf_is_not_invoked_when_not_configured(self):
        cert = _make_certificate_to_pdf(config=dict(_BASE_CONFIG))

        with patch(
            "nau.course.certificate.course_certificate_to_pdf.render_pdf", return_value=b"pdf-bytes"
        ), patch("nau.course.certificate.course_certificate_to_pdf.digital_sign_pdf") as mock_sign:
            result = cert.generate_new_certificate_to_dest_format()

        assert result == b"pdf-bytes"
        mock_sign.assert_not_called()


class TestLimitPages:
    def test_cut_pdf_limit_pages_is_called_when_the_limit_meta_is_present(self):
        cert = _make_certificate_to_pdf(metas={"nau-course-certificate-limit-pages": "3"})

        with patch(
            "nau.course.certificate.course_certificate_to_pdf.render_pdf", return_value=b"pdf-bytes"
        ), patch(
            "nau.course.certificate.course_certificate_to_pdf.cut_pdf_limit_pages", return_value=b"cut-pdf-bytes"
        ) as mock_cut:
            result = cert.generate_new_certificate_to_dest_format()

        assert result == b"cut-pdf-bytes"
        mock_cut.assert_called_once_with(b"pdf-bytes", 0, 3)

    def test_cut_pdf_limit_pages_is_not_called_when_the_meta_is_absent(self):
        cert = _make_certificate_to_pdf()

        with patch(
            "nau.course.certificate.course_certificate_to_pdf.render_pdf", return_value=b"pdf-bytes"
        ), patch("nau.course.certificate.course_certificate_to_pdf.cut_pdf_limit_pages") as mock_cut:
            result = cert.generate_new_certificate_to_dest_format()

        assert result == b"pdf-bytes"
        mock_cut.assert_not_called()


class TestGetFilenamePdf:
    def test_meta_value_takes_priority_over_everything_else(self):
        cert = _make_certificate_to_pdf(
            config={**_BASE_CONFIG, "CERTIFICATE_FILE_NAME": "config-default.pdf"},
            metas={"nau-course-certificate-filename": "from-meta.pdf"},
        )

        assert cert.get_filename() == "from-meta.pdf"

    def test_config_default_used_when_meta_is_absent(self):
        cert = _make_certificate_to_pdf(config={**_BASE_CONFIG, "CERTIFICATE_FILE_NAME": "config-default.pdf"})

        assert cert.get_filename() == "config-default.pdf"

    def test_hardcoded_default_used_when_neither_meta_nor_config_are_set(self):
        cert = _make_certificate_to_pdf(config=dict(_BASE_CONFIG))

        assert cert.get_filename() == "certificate.pdf"


class TestImageFormat:
    def test_meta_value_overrides_the_default_format(self):
        cert = _make_certificate_to_image(metas={"imgkit-format": "png"})

        assert cert.image_format() == "png"

    def test_defaults_to_jpeg_when_no_meta_is_present(self):
        cert = _make_certificate_to_image()

        assert cert.image_format() == "jpeg"

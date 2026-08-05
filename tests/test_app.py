"""
Tests for the Flask routes and config-loading helper in app.py.

CourseCertificateToPDF/CourseCertificateToImage and Configuration are
mocked at their app.py import sites so these tests exercise only the
routing/response-building logic, not the certificate rendering pipeline
(which is covered by tests/test_course_certificate_to_pdf.py and
tests/test_certificate_renderer.py).
"""
from unittest.mock import MagicMock, patch

import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.app.testing = True
    with app_module.app.test_client() as client:
        yield client


def _mock_pdf_converter(filename="certificate.pdf", binary=b"%PDF-fake-bytes"):
    instance = MagicMock()
    instance.get_filename.return_value = filename
    instance.convert.return_value = binary
    return instance


def _mock_image_converter(filename="certificate.jpg", image_format="jpeg", binary=b"fake-jpeg-bytes"):
    instance = MagicMock()
    instance.get_filename.return_value = filename
    instance.image_format.return_value = image_format
    instance.convert.return_value = binary
    return instance


class TestInlineRoute:

    def test_returns_the_pdf_with_inline_content_disposition(self, client):
        mock_instance = _mock_pdf_converter(filename="my-certificate.pdf", binary=b"pdf-bytes")

        with patch.object(app_module, "read_config", return_value={}), patch.object(
            app_module, "CourseCertificateToPDF", return_value=mock_instance
        ):
            response = client.get("/inline/some/course/path")

        assert response.status_code == 200
        assert response.data == b"pdf-bytes"
        assert response.headers["Content-Type"] == "application/pdf"
        assert response.headers["Content-Disposition"] == "inline; filename=my-certificate.pdf"


class TestAttachmentRoute:

    def test_returns_the_pdf_with_attachment_content_disposition(self, client):
        mock_instance = _mock_pdf_converter(filename="my-certificate.pdf", binary=b"pdf-bytes")

        with patch.object(app_module, "read_config", return_value={}), patch.object(
            app_module, "CourseCertificateToPDF", return_value=mock_instance
        ):
            response = client.get("/attachment/some/course/path")

        assert response.status_code == 200
        assert response.data == b"pdf-bytes"
        assert response.headers["Content-Type"] == "application/pdf"
        assert response.headers["Content-Disposition"] == "attachment; filename=my-certificate.pdf"

    def test_forwards_the_path_and_query_string_to_the_converter(self, client):
        mock_instance = _mock_pdf_converter()

        with patch.object(app_module, "read_config", return_value={}), patch.object(
            app_module, "CourseCertificateToPDF", return_value=mock_instance
        ) as mock_class:
            client.get("/attachment/courses/abc/certificate?lang=pt")

        args = mock_class.call_args[0]
        assert args[1] == "courses/abc/certificate"
        assert args[2] == b"lang=pt"


class TestImageRoute:

    def test_returns_the_image_with_the_format_specific_content_type(self, client):
        mock_instance = _mock_image_converter(
            filename="my-certificate.png", image_format="png", binary=b"png-bytes"
        )

        with patch.object(app_module, "read_config", return_value={}), patch.object(
            app_module, "CourseCertificateToImage", return_value=mock_instance
        ):
            response = client.get("/image/some/course/path")

        assert response.status_code == 200
        assert response.data == b"png-bytes"
        assert response.headers["Content-Type"] == "image/png"
        # Images are always served inline, regardless of route name.
        assert response.headers["Content-Disposition"] == "inline; filename=my-certificate.png"


class TestReadConfig:

    def test_returns_the_config_yml_contents_when_present_and_non_empty(self):
        mock_config = MagicMock()
        mock_config.config.return_value = {"LMS_SERVER_URL": "https://lms.example.test"}

        with patch.object(app_module, "Configuration", return_value=mock_config) as mock_configuration_class:
            result = app_module.read_config()

        mock_configuration_class.assert_called_once_with("config.yml")
        assert result == {"LMS_SERVER_URL": "https://lms.example.test"}

    def test_falls_back_to_default_config_yml_when_config_yml_is_empty(self):
        empty_config = MagicMock()
        empty_config.config.return_value = None
        default_config = MagicMock()
        default_config.config.return_value = {"LOGGING": {"version": 1}}

        with patch.object(
            app_module, "Configuration", side_effect=[empty_config, default_config]
        ) as mock_configuration_class:
            result = app_module.read_config()

        assert mock_configuration_class.call_args_list[0].args == ("config.yml",)
        assert mock_configuration_class.call_args_list[1].args == ("default-config.yml",)
        assert result == {"LOGGING": {"version": 1}}

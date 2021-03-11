import logging
import logging.config
from abc import ABC, abstractmethod
from builtins import dict, str

import boto3
import imgkit
import pdfkit
import requests
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from nau.course.certificate.configuration import Configuration
from nau.course.certificate.cut_pdf import cut_pdf_limit_pages
from requests.auth import HTTPBasicAuth
from nau.course.certificate.digital_sign_pdf import digital_sign_pdf

from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class CourseCertificateToBase(ABC):
    '''
    Converts an URL certificate to a PDF. If the URL contains a certificate id then save it to a S3 Bucket.
    On the 2nd request of that certificate returns the previous one.
    If the certificate template have been changed and also its HTTP meta version then a new PDF is generated.
    '''
    _config = None
    _path : str = None
    _url = None
    _certificate_id = None
    _certificate_metas = None

    def __init__(self, config: Configuration, path: str, query_string: str):
        self._config = config

        # https://www.digitalocean.com/community/tutorials/how-to-use-logging-in-python-3
        # https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
        logging.config.dictConfig(self._config.get('LOGGING'))

        self._path = path
        # parse query string to a dict where its value is a list.
        query_string_dict : dict = parse_qs(query_string.decode('ascii'))
        # Get query parameter 'language' that will be binded to the HTTP header 'Accept-Language' 
        # for the request that generates the PDF
        language_query_values = query_string_dict.get("language", None)
        self._language = language_query_values[0] if language_query_values else None

        # https://lms.dev.nau.fccn.pt
        lms_server_url = self._config['LMS_SERVER_URL']
        self._url = lms_server_url + '/' + path
        if query_string and len(query_string) > 0:
            self._url += "?" + query_string.decode('ascii')

        certificates_prefix = 'certificates/'
        if (path.startswith(certificates_prefix)):
            self._certificate_id = path[len(certificates_prefix):len(path)]

        self._certificate_metas = self.load_certificate_http_metas(self._url, self.http_header_name(
        ), self.http_header_value(), self.lms_servers_auth_user(), self.lms_servers_auth_pass())

    def convert(self):
        '''
        Receives and URL and returns the binary PDF.
        '''
        logger.info(
            "Converting html certificate to PDF with URL: {}".format(self._url))

        certificate_version = self._get_certificate_http_meta(
            self.http_header_meta_version_name())
        logger.info("certificate_version: {}".format(certificate_version))
        s3_bucket_certificate_key = self._path + '/' + \
            (certificate_version if certificate_version else self.bucket_no_version()).replace(
                ' ', '_') + self.s3_suffix()

        binary_output = None
        if (self._certificate_id is not None):
            binary_output = self.get_certificate_on_s3_bucket(
                self.bucket_name(),
                self.bucket_endpoint_url(),
                self.aws_access_key_id(),
                self.aws_secret_access_key(),
                s3_bucket_certificate_key
            )

        if (binary_output is None):
            binary_output = self.generate_new_certificate_to_dest_format()

        if (self._certificate_id is not None):
            self.save_certificate(s3_bucket_certificate_key, binary_output)

        return binary_output

    @abstractmethod
    def generate_new_certificate_to_dest_format(self):
        raise NotImplementedError("To be redefined in subclasses")

    @abstractmethod
    def s3_suffix(self):
        raise NotImplementedError("To be redefined in subclasses")

    def http_header_name(self):
        return self._config['HTTP_HEADER_NAME']

    def http_header_meta_prefix(self):
        return self._config['HTTP_HEADER_META_PREFIX']

    def http_header_value(self):
        return str(self._config['HTTP_HEADER_VALUE'])

    def bucket_name(self):
        return self._config['BUCKET_NAME']

    def aws_access_key_id(self):
        return self._config['BUCKET_AWS_ACCESS_KEY_ID']

    def aws_secret_access_key(self):
        return self._config['BUCKET_AWS_SECRET_ACCESS_KEY']

    def bucket_endpoint_url(self):
        return self._config['BUCKET_ENDPOINT_URL']

    def http_header_meta_version_name(self):
        return self._config['HTTP_HEADER_META_VERSION_NAME']

    def http_header_meta_filename_name(self):
        return self._config['HTTP_HEADER_META_FILENAME_NAME']

    def http_header_meta_limit_number_pages(self):
        return self._config.get('HTTP_HEADER_META_LIMIT_NUMBER_PAGES', None)

    def bucket_no_version(self):
        return self._config['BUCKET_CERTIFICATE_NO_VERSION_KEY']

    def lms_servers_auth_user(self):
        return self._config.get('LMS_SERVER_AUTH_USER', None)

    def lms_servers_auth_pass(self):
        return self._config.get('LMS_SERVER_AUTH_PASS', None)

    def http_header_meta_image_filename_name(self):
        return self._config['HTTP_HEADER_META_IMAGE_FILENAME_NAME']

    def http_header_meta_image_prefix(self):
        return self._config['HTTP_HEADER_META_IMAGE_PREFIX']

    def http_header_meta_image_format(self):
        return self._config.get('HTTP_HEADER_META_IMAGE_FORMAT', 'imgkit-format')

    def _get_certificate_http_meta(self, metaName: str, default=None):
        '''
        Get the value of a meta HTTP header of the certificate.
        '''
        if metaName is not None:
            for meta in self._certificate_metas:
                if 'name' in meta.attrs and meta.attrs['name'] == metaName:
                    return meta.attrs['content']
        return default

    @staticmethod
    def get_certificate_on_s3_bucket(bucket_name: str, endpoint_url: str, aws_access_key_id: str, aws_secret_access_key: str, certificate_s3_key: str) -> bytes:
        """
        Get the PDF certificate on a S3 Bucket. The key on the S3 Bucket is the certificate URL itself.

        Args:
            bucket_name (str): The S3 bucket name were the certificate are being saved.
            endpoint_url (str): The endpoint URL of the S3 server
            aws_access_key_id (str): The access key identification to be used to connect to S3
            aws_secret_access_key (str): The secret access key to be used to connect to S3
            certificate_s3_key (str): The key used to get the certificate

        Returns:
            bytes: The PDF certiticate on S3 bucket
        """
        s3_client = boto3.client('s3', use_ssl=False, aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url)
        try:
            s3_response_object = s3_client.get_object(
                Bucket=bucket_name, Key=certificate_s3_key)
            object_content = s3_response_object['Body'].read()
            return object_content
        except ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                logger.info("Course certificate not found on storage s3 for key '{0}' exception: {1}".format(certificate_s3_key, e))
            else:
                logger.error("Received error: {0}".format(e), exc_info=True)
            return None

    def save_certificate(self, certificate_s3_key, binary_output):
        self.save_certificate_on_s3_bucket(self.bucket_name(), self.bucket_endpoint_url(
        ), self.aws_access_key_id(), self.aws_secret_access_key(), certificate_s3_key, binary_output)

    @staticmethod
    def save_certificate_on_s3_bucket(bucket_name, endpoint_url, aws_access_key_id, aws_secret_access_key, certificate_s3_key, binary):
        s3_client = boto3.client('s3', use_ssl=False, aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url)
        s3_client.put_object(
            Body=binary, Bucket=bucket_name, Key=certificate_s3_key)

    @staticmethod
    def load_certificate_http_metas(url, http_header_name, http_header_value, lms_servers_auth_user, lms_servers_auth_pass):
        '''
        Extracts a dictionary with all HTTP meta headers.
        '''
        logger.info("url {}".format(url))
        request_headers = {http_header_name: http_header_value}
        auth = None
        if lms_servers_auth_user is not None and lms_servers_auth_pass is not None:
            auth = HTTPBasicAuth(lms_servers_auth_user, lms_servers_auth_pass)
        response = requests.get(url, headers=request_headers, auth=auth)
        soup = BeautifulSoup(response.text, features="html.parser")

        return soup.find_all('meta')

    def extract_specific_http_metas(self, http_header_meta_prefix):
        '''
        Get pdf kit certificate meta headers, those that are prefixed with http_header_meta_prefix value. Eg. pdfkit-
        '''
        http_metas = dict()
        for meta in self._certificate_metas:
            if 'name' in meta.attrs and meta.attrs['name'].startswith(http_header_meta_prefix):
                http_metas.update({meta.attrs['name']: meta.attrs['content']})

        # Remove pdf_kit prefix from each options dict key.
        return {key.replace(http_header_meta_prefix, ''): value for key, value in http_metas.items()}

    def generate_options(self, http_header_meta_prefix: str) -> dict:
        options_extracted_on_http_metas = self.extract_specific_http_metas(
            http_header_meta_prefix)

        custom_headers = []
        if self.http_header_name() is not None and self.http_header_value() is not None:
            custom_headers.append((self.http_header_name(), self.http_header_value()))
        
        if self._language:
            # Add the HTTP Header 'Accept-Language' if a specific language was passed on the query string
            custom_headers.append(("Accept-Language", self._language))
        
        options_force_show_certificate_content = { 'custom-header': custom_headers }

        options = {**options_force_show_certificate_content,
                   **options_extracted_on_http_metas}

        logger.info(options_extracted_on_http_metas)
        return options


class CourseCertificateToPDF(CourseCertificateToBase):
    '''
    Convert a course certificate to a PDF.
    '''

    def __init__(self, config: Configuration, path: str, query_string: str):
        super().__init__(config, path, query_string)

    def get_filename(self):
        filename = self._get_certificate_http_meta(
            self.http_header_meta_filename_name())
        return filename if filename is not None else self._config['CERTIFICATE_FILE_NAME']

    def s3_suffix(self):
        return ".pdf"

    def generate_new_certificate_to_dest_format(self):
        options = self.generate_options(self.http_header_meta_prefix())

        pdf = pdfkit.from_url(self._url, False, options=options)

        limit_pages = self._get_certificate_http_meta(
            self.http_header_meta_limit_number_pages())
        if (limit_pages is not None):
            pdf = cut_pdf_limit_pages(pdf, 0, int(limit_pages))
        
        digital_sign_config = self._config.get("DIGITAL_SIGNATURE")
        if digital_sign_config is not None:
            pdf = digital_sign_pdf(pdf, digital_sign_config, self._language)

        return pdf


class CourseCertificateToImage(CourseCertificateToBase):
    '''
    Generate a course certificate to an image.
    '''

    def __init__(self, config: Configuration, path: str, query_string: str):
        super().__init__(config, path, query_string)

    def get_filename(self):
        return self._get_certificate_http_meta(self.http_header_meta_image_filename_name(), self._config.get('CERTIFICATE_IMAGE_FILE_NAME', 'certificate')) + \
            '.' + \
            self.image_format()

    def image_format(self):
        return self._get_certificate_http_meta(self.http_header_meta_image_format(), 'jpeg')

    def s3_suffix(self):
        return "." + self.image_format()

    def generate_new_certificate_to_dest_format(self):
        options = self.generate_options(self.http_header_meta_image_prefix())
        return imgkit.from_url(self._url, False, options=options)

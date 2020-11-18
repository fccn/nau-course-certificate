import logging
import logging.config
import requests
import pdfkit
from bs4 import BeautifulSoup
from builtins import dict, str
import boto3
from botocore.exceptions import ClientError
from nau.course.certificate.configuration import Configuration
from nau.course.certificate.cut_pdf import cut_pdf_limit_pages
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

class CourseCertificateToPDF:
    '''
    Converts an URL certificate to a PDF. If the URL contains a certificate id then save it to a S3 Bucket.
    On the 2nd request of that certificate returns the previous one.
    If the certificate template have been changed and also its HTTP meta version then a new PDF is generated.
    '''
    _config = None
    _path = None
    _url = None
    _certificate_id = None
    _certificate_metas = None

    def __init__(self, config:Configuration, path:str, query_string:str):
        self._config = config

        # https://www.digitalocean.com/community/tutorials/how-to-use-logging-in-python-3
        # https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
        logging.config.dictConfig(self._config.get('LOGGING'))

        self._path = path
        self._query_string = query_string
        lms_server_url = self._config['LMS_SERVER_URL'] # https://lms.dev.nau.fccn.pt
        self._url = lms_server_url + '/' + path
        if query_string and len(query_string) > 0:
            self._url += "?" + self._query_string.decode('ascii')

        certificates_prefix = 'certificates/'
        if (path.startswith(certificates_prefix)):
            self._certificate_id = path[len(certificates_prefix):len(path)]

        self._certificate_metas = self.load_certificate_http_metas(self._url, self.http_header_name(), self.http_header_value(), self.lms_servers_auth_user(), self.lms_servers_auth_pass())

    def convert(self):
        '''
        Receives and URL and returns the binary PDF.
        '''
        logger.info("Converting html certificate to PDF with URL: {}".format(self._url))

        certificate_version = self.get_certificate_http_meta_version_value()
        logger.info("certificate_version: {}".format(certificate_version))
        s3_bucket_certificate_key = self._path + '/' + ( certificate_version if certificate_version else self.bucket_no_version()).replace(' ', '_')
        pdf = None
        if (self._certificate_id is not None):
            pdf = self.get_certificate_on_s3_bucket(self.bucket_name(), self.bucket_endpoint_url(), self.aws_access_key_id(), self.aws_secret_access_key(), s3_bucket_certificate_key)

        if (pdf is None):
            pdf = self.generate_new_certificate_to_pdf()

            limit_pages = self._get_certificate_http_meta_limit_number_pages()
            if (limit_pages is not None):
                pdf = cut_pdf_limit_pages(pdf, 0, int(limit_pages))

        if (self._certificate_id is not None):
            self.save_certificate(s3_bucket_certificate_key, pdf)

        return pdf

    def get_filename(self):
        filename = self._get_certificate_http_meta_filename_value()
        return filename if filename is not None else self._config['CERTIFICATE_FILE_NAME']

    def save_certificate(self, certificate_s3_key, pdf):
        self.save_certificate_on_s3_bucket(self.bucket_name(), self.bucket_endpoint_url(), self.aws_access_key_id(), self.aws_secret_access_key(), certificate_s3_key, pdf)

    def generate_new_certificate_to_pdf(self):
        extracted_pdfkit_http_metas = self.extract_pdfkit_http_metas();
        options_extracted_on_http_metas = self.removePdfKitPrefix(extracted_pdfkit_http_metas)

        options_force_show_certificate_content = {
            'custom-header' : [
               (self.http_header_name(), self.http_header_value())
           ]
        }

        options = {**options_force_show_certificate_content, **options_extracted_on_http_metas}

        logger.info(options_extracted_on_http_metas)

        pdf = pdfkit.from_url(self._url, False, options=options)

        return pdf

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

    @staticmethod
    def get_certificate_on_s3_bucket(bucket_name:str, endpoint_url, aws_access_key_id, aws_secret_access_key, certificate_s3_key):
        '''
        Get the PDF certificate on a S3 Bucket. The key on the S3 Bucket is the certificate URL itself.
        '''
        s3_client = boto3.client('s3', use_ssl=False, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url)
        try:
            s3_response_object = s3_client.get_object(Bucket=bucket_name, Key=certificate_s3_key)
            object_content = s3_response_object['Body'].read()
            return object_content
        except ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                logger.info("NoSuchKey: {0}".format(e), exc_info=True)
            else:
                logger.error("Received error: {0}".format(e), exc_info=True)
            return None

    @staticmethod
    def save_certificate_on_s3_bucket(bucket_name, endpoint_url, aws_access_key_id, aws_secret_access_key, certificate_s3_key, pdf):
        s3_client = boto3.client('s3', use_ssl=False, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url)
        s3_client.put_object(Body=pdf, Bucket=bucket_name, Key=certificate_s3_key)

    def get_certificate_http_meta_version_value(self):
        '''
        Get the value of the certificate HTTP meta version.
        '''
        return self._get_certificate_http_meta(self.http_header_meta_version_name())

    def _get_certificate_http_meta_filename_value(self):
        '''
        Get the value of the certificate HTTP meta version.
        '''
        return self._get_certificate_http_meta(self.http_header_meta_filename_name())

    def _get_certificate_http_meta_limit_number_pages(self):
        '''
        Get the value of the certificate HTTP meta limit number of pages.
        '''
        return self._get_certificate_http_meta(self.http_header_meta_limit_number_pages())

    def _get_certificate_http_meta(self, metaName:str):
        '''
        Get the value of a meta HTTP header of the certificate.
        '''
        if metaName is not None:
            for meta in self._certificate_metas:
                if 'name' in meta.attrs and meta.attrs['name'] == metaName:
                    return meta.attrs['content']
        return None

    @staticmethod
    def load_certificate_http_metas(url, http_header_name, http_header_value, lms_servers_auth_user, lms_servers_auth_pass):
        '''
        Extracts a dictionary with all HTTP meta headers.
        '''
        logger.info("url {}".format(url))
        request_headers = { http_header_name : http_header_value }
        auth = None
        if lms_servers_auth_user is not None and lms_servers_auth_pass is not None:
            auth = HTTPBasicAuth(lms_servers_auth_user, lms_servers_auth_pass)
        response = requests.get(url, headers=request_headers, auth=auth)
        soup = BeautifulSoup(response.text, features="html.parser")

        return soup.find_all('meta')

    def extract_pdfkit_http_metas(self):
        '''
        Get pdf kit certificate meta headers, those that are prefixed with with the value of the configuration HTTP_HEADER_META_PREFIX (pdfkit_).
        '''
        pdfkit_metas = dict()
        for meta in self._certificate_metas:
            if 'name' in meta.attrs and meta.attrs['name'].startswith(self.http_header_meta_prefix()):
                pdfkit_metas.update( { meta.attrs['name'] : meta.attrs['content']} )

        return pdfkit_metas

    def removePdfKitPrefix(self, options):
        '''
        Remove pdf_kit prefix from each options dict key.
        '''
        return {key.replace(self.http_header_meta_prefix(), ''): value for key, value in options.items()}

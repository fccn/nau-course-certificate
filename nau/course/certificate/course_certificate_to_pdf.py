import requests
import pdfkit
import logging as log
from bs4 import BeautifulSoup
from builtins import dict, str
import boto3
from botocore.exceptions import ClientError
from nau.course.certificate.configuration import Configuration

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

    def __init__(self, config:Configuration, path:str):
        self._config = config
        self._path = path
        lms_server_url = self._config['LMS_SERVER_URL'] # https://lms.dev.nau.fccn.pt
        self._url = lms_server_url + '/' + path

        certificates_prefix = 'certificates/'
        if (path.startswith(certificates_prefix)):
            self._certificate_id = path[len(certificates_prefix):len(path)]

        self._certificate_metas = self.load_certificate_http_metas(self._url, self.http_header_name(), self.http_header_value())

    def convert(self):
        '''
        Receives and URL and returns the binary PDF.
        '''
        log.debug("Converting html certificate to PDF with URL: {}".format(self._url))

        certificate_version = self.get_certificate_http_meta_version_value()
        s3_bucket_certificate_key = self._path + '/' + ( certificate_version if certificate_version else self.bucket_no_version()).replace(' ', '_')
        pdf = None
        if (self._certificate_id is not None):
            pdf = self.get_certificate_on_s3_bucket(self.bucket_name(), self.bucket_endpoint_url(), self.aws_access_key_id(), self.aws_secret_access_key(), s3_bucket_certificate_key)

        if (pdf is None):
            pdf = self.generate_new_certificate_to_pdf()

        if (self._certificate_id is not None):
            self.save_certificate(s3_bucket_certificate_key, pdf)

        return pdf

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

        log.info(options_extracted_on_http_metas)

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

    def bucket_no_version(self):
        return self._config['BUCKET_CERTIFICATE_NO_VERSION_KEY']

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
                log.info("NoSuchKey: {0}".format(e), exc_info=True)
            else:
                log.error("Received error: {0}".format(e), exc_info=True)
            return None

    @staticmethod
    def save_certificate_on_s3_bucket(bucket_name, endpoint_url, aws_access_key_id, aws_secret_access_key, certificate_s3_key, pdf):
        s3_client = boto3.client('s3', use_ssl=False, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url)
        s3_client.put_object(Body=pdf, Bucket=bucket_name, Key=certificate_s3_key)

    def get_certificate_http_meta_version_value(self):
        '''
        Get the value of the certificate HTTP meta version.
        '''
        for meta in self._certificate_metas:
            if 'name' in meta.attrs and meta.attrs['name'] == self.http_header_meta_version_name():
                return meta.attrs['content']
        return None

    @staticmethod
    def load_certificate_http_metas(url, http_header_name, http_header_value):
        '''
        Extracts a dictionary with all HTTP meta headers.
        '''
        request_headers = { http_header_name : http_header_value }
        response = requests.get(url, headers=request_headers)
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

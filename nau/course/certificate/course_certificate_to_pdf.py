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
    Class that converts and URL to a certificate to a PDF
    '''

    _config = None
    _path = None
    _url = None
    _certificate_id = None

    def __init__(self, config:Configuration, path:str):
        self._config = config
        self._path = path
        lms_server_url = self._config['LMS_SERVER_URL'] # https://lms.dev.nau.fccn.pt
        self._url = lms_server_url + '/' + path

        certificates_prefix = '/certificates/'
        if (path.startswith(certificates_prefix)):
            self._certificate_id = path.substring(certificates_prefix.length)

    def convert(self):
        '''
        Receives and URL and returns the binary PDF.
        '''
        log.debug("Converting html certificate to PDF with URL: {}".format(self._url))

        pdf = None
        if (self._certificate_id is not None):
            pdf = self.get_certificate_on_s3_bucket(self.bucket_name(), self.bucket_endpoint_url(), self.aws_access_key_id(), self.aws_secret_access_key(), self._path)

        if (pdf is None):
            pdf = self.generate_new_certificate_to_pdf()
            self.save_certificate(pdf)

        return pdf

    def save_certificate(self, pdf):
        self.save_certificate_on_s3_bucket(self.bucket_name(), self.bucket_endpoint_url(), self.aws_access_key_id(), self.aws_secret_access_key(), self._path, pdf)

    def generate_new_certificate_to_pdf(self):
        extracted_pdfkit_http_metas = self.extract_options_on_http_metas(self._url);
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

    @staticmethod
    def get_certificate_on_s3_bucket(bucket_name:str, endpoint_url, aws_access_key_id, aws_secret_access_key, certificate_s3_key):
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

    def extract_options_on_http_metas(self, url):
        '''
        Extracts a dictionary with all HTTP meta headers on the url that it's prefixed with the configuration HTTP_HEADER_META_PREFIX (pdfkit_).
        '''
        request_headers = { self.http_header_name() : self.http_header_value() }
        response = requests.get(url, headers=request_headers)
        soup = BeautifulSoup(response.text, features="html.parser")

        metas = soup.find_all('meta')
        pdfkit_metas = dict()

        for meta in metas:
            if 'name' in meta.attrs and meta.attrs['name'].startswith(self.http_header_meta_prefix()):
                pdfkit_metas.update( { meta.attrs['name'] : meta.attrs['content']} )

        return pdfkit_metas

    def removePdfKitPrefix(self, options):
        '''
        Remove pdf_kit prefix from each options dict key.
        '''
        return {key.replace(self.http_header_meta_prefix(), ''): value for key, value in options.items()}

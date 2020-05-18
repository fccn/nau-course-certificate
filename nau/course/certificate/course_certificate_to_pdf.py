import requests
import pdfkit
import logging as log
from bs4 import BeautifulSoup
from builtins import dict

'''
Class that converts and URL to a certificate to a PDF
'''
class CourseCertificateToPDF:

    def __init__(self, config):
        self._config = config

    def convert(self, url):
        log.debug("Converting html certificate to PDF with URL: {}".format(url))
        '''
        Receives and URL and returns the binary PDF.
        '''

        extracted_pdfkit_http_metas = self.extract_options_on_http_metas(url);
        options_extracted_on_http_metas = self.removePdfKitPrefix(extracted_pdfkit_http_metas)

        options_force_show_certificate_content = {
            'custom-header' : [
               (self.http_header_name(), self.http_header_value())
           ]
        }

        options = {**options_force_show_certificate_content, **options_extracted_on_http_metas}

        print(options_extracted_on_http_metas)

        pdf = pdfkit.from_url(url, False, options=options)

        return pdf

    def http_header_name(self):
        return self._config['HTTP_HEADER_NAME']

    def http_header_meta_prefix(self):
        return self._config['HTTP_HEADER_META_PREFIX']

    def http_header_value(self):
        return str(self._config['HTTP_HEADER_VALUE'])

    def extract_options_on_http_metas(self, url):
        '''
        Extracts a dictionary with all HTTP meta headers on the url that it's prefixed with 'pdfkit_'
        '''
        request_headers = { self.http_header_name() : self.http_header_value() }
        response = requests.get(url, headers=request_headers)
        soup = BeautifulSoup(response.text)

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

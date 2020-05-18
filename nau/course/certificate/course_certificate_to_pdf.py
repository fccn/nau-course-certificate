import pdfkit
import logging as log

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
        http_header_name = self._config['HTTP_HEADER_NAME']
        http_header_value = str(self._config['HTTP_HEADER_VALUE'])

        pdf = pdfkit.from_url(url, False, options={
            'custom-header' : [
               (http_header_name, http_header_value)
           ]
        })

        return pdf

import pdfkit

'''
Class that converts and URL to a certificate to a PDF
'''
class CourseCertificateToPDF:

    def __init__(self, config):
        self._config = config

    def convert(self, url):
        '''
        Receives and URL and returns the binary PDF.
        '''
        http_header_name = self._config['HTTP_HEADER_NAME']
        http_header_value = self._config['HTTP_HEADER_VALUE']

        pdf = pdfkit.from_url(url, False, options={
            'custom-header' : [
               (http_header_name, http_header_value)
           ]
        })

        return pdf

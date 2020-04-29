import pdfkit

'''
Class that converts and URL to a certificate to a PDF
'''
class CourseCertificateToPDF:

    #def __init__(self, config):

    def convert(self, url):
        '''
        Receives and URL and returns the binary PDF.
        '''
        http_header_name = 'X-NAU-Certificate-force-html'
        http_header_value = 'true'

        pdf = pdfkit.from_url(url, False, options={
            'custom-header' : [
               (http_header_name, http_header_value)
           ]
        })

        return pdf

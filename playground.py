# Playground script
#
from nau.course.certificate import CourseCertificateToPDF
import configparser

config_parser = configparser.ConfigParser()
url = 'https://lms.dev.nau.fccn.pt/certificates/5a65166eaf8f44e388d9bd8bb082bace'
config = config_parser.read('default_settings.cfg')

# request = urllib.request.Request(url)
# request.add_header(http_header_name, http_header_value)
# response = urllib.request.urlopen(request)
# content = response.read().decode('utf-8')

# print(content)

# pdf = pdfkit.from_string(content, False)

# pdf = pdfkit.from_url(url, False, options={
# 	'custom-header' : [
#        (http_header_name, http_header_value)
#    ]
# })

print(config)

binary_pdf = CourseCertificateToPDF(config).convert(url)

file = open("out.pdf", "wb") # w to write, b in binary mode
file.write(binary_pdf)
file.close()

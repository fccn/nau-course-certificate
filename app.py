from flask import Flask, render_template, request, make_response
from nau.course.certificate import CourseCertificateToPDF

app = Flask(__name__)
#app.config.from_object('config')

# To start
# export NAU_COURSE_CERTIFICATE_CONFIGURATION=/path/to/settings.cfg
#
#if 'NAU_COURSE_CERTIFICATE_CONFIGURATION' in os.environ:
#    app.config.from_envvar('NAU_COURSE_CERTIFICATE_CONFIGURATION')

#@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def redirect(path):

    # TODO change it to configuration
    lms_server_url = 'https://lms.dev.nau.fccn.pt'
    certificate_file_name = 'certificate.pdf'
    # change inline to attachment if you want the file to download rather than display in the browser
    content_disposition = 'inline'
    url = lms_server_url + '/' + path

    binary_pdf = CourseCertificateToPDF().convert(url)

    response = make_response(binary_pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = '{}; filename={}'.format(content_disposition, certificate_file_name)
    return response

# startup the Flask web server
if __name__ == '__main__':
    app.run()

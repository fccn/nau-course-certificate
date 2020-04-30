from flask import Flask
from flask import make_response
from nau.course.certificate import CourseCertificateToPDF

app = Flask(__name__)

# Load default configurations
app.config.from_pyfile('default_settings.cfg')

# Load if exists the application configuration
app.config.from_pyfile('config.cfg', silent=True)

# Load if exists custom configuration from a file referenced on a environment variable
# Define environment variable like:
# export NAU_COURSE_CERTIFICATE_CONFIGURATION=/path/to/settings.cfg
app.config.from_envvar('NAU_COURSE_CERTIFICATE_CONFIGURATION', silent=True)

#@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def redirect(path):

    lms_server_url = app.config['LMS_SERVER_URL'] # https://lms.dev.nau.fccn.pt
    certificate_file_name = app.config['CERTIFICATE_FILE_NAME'] # certificate.pdf
    # change inline to attachment if you want the file to download rather than display in the browser
    content_disposition = 'inline'
    url = lms_server_url + '/' + path

    binary_pdf = CourseCertificateToPDF(app.config).convert(url)

    response = make_response(binary_pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = '{}; filename={}'.format(content_disposition, certificate_file_name)
    return response

# startup the Flask web server
if __name__ == '__main__':
    app.run()

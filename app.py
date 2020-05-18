from flask import (Flask, send_from_directory)
from flask import make_response
import os
from nau.course.certificate.course_certificate_to_pdf import CourseCertificateToPDF
from nau.course.certificate.configuration import Configuration

app = Flask(__name__)

def convert_certificate_to_pdf(content_disposition, path):
    configuration = Configuration('config.yml')
    config = configuration.config()

    lms_server_url = config['LMS_SERVER_URL'] # https://lms.dev.nau.fccn.pt
    certificate_file_name = config['CERTIFICATE_FILE_NAME'] # certificate.pdf
    # change inline to attachment if you want the file to download rather than display in the browser
    url = lms_server_url + '/' + path

    binary_pdf = CourseCertificateToPDF(config).convert(url)

    response = make_response(binary_pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = '{}; filename={}'.format(content_disposition, certificate_file_name)
    return response

@app.route('/inline/<path:path>')
def inline(path):
    return convert_certificate_to_pdf("inline", path)

@app.route('/attachment/<path:path>')
def attachment(path):
    return convert_certificate_to_pdf("attachment", path)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# startup the Flask web server
if __name__ == '__main__':
    app.run()

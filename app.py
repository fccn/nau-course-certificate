from flask import Flask, abort, request, send_from_directory
from flask import make_response
from nau.course.certificate.course_certificate_to_pdf import CourseCertificateToPDF, CourseCertificateToImage, get_lms_server_url
from nau.course.certificate.qrcode_generator import generate_certificate_qrcode_svg
from nau.course.certificate.configuration import Configuration

app = Flask(__name__, static_folder='static')

def read_config():
    configuration = Configuration('config.yml')
    config = configuration.config()
    if not config:
        configuration = Configuration('default-config.yml')
        config = configuration.config()
    return config

def convert_certificate_to_pdf(content_disposition, path, query_string):
    config = read_config()

    course_certificate_to_pdf = CourseCertificateToPDF(config, path, query_string)
    certificate_file_name = course_certificate_to_pdf.get_filename()
    binary_pdf = course_certificate_to_pdf.convert()

    response = make_response(binary_pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = '{}; filename={}'.format(content_disposition, certificate_file_name)
    return response

@app.route('/inline/<path:path>')
def inline(path):
    return convert_certificate_to_pdf("inline", path, request.query_string)

@app.route('/attachment/<path:path>')
def attachment(path):
    return convert_certificate_to_pdf("attachment", path, request.query_string)

@app.route('/favicon.ico')
@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/image/<path:path>')
def image(path):
    config = read_config()

    course_certificate_to_image = CourseCertificateToImage(config, path, request.query_string)
    certificate_file_name = course_certificate_to_image.get_filename()
    binary_result = course_certificate_to_image.convert()

    response = make_response(binary_result)
    response.headers['Content-Type'] = 'image/' + course_certificate_to_image.image_format()
    response.headers['Content-Disposition'] = '{}; filename={}'.format('inline', certificate_file_name)
    return response

@app.route('/qrcode/<path:path>')
def qrcode(path):
    '''
    QR code (SVG) with a link to the public LMS page of the certificate, e.g. `/qrcode/certificates/<id>`.
    The optional `color` query parameter is a hex color, like `ffffff`, and the background is transparent.
    '''
    try:
        svg = generate_certificate_qrcode_svg(get_lms_server_url(read_config()), path, request.args.get('color'))
    except ValueError:
        abort(404)

    response = make_response(svg)
    response.headers['Content-Type'] = 'image/svg+xml'
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response

# startup the Flask web server
if __name__ == '__main__':
    app.run()

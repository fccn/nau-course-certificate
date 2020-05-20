
## Development

```bash
virtualenv venv --python=python3
source venv/bin/activate
python -m pip install -r requirements.txt --upgrade
```

Change the certificate template on openedx LMS on https://lms.dev.nau.fccn.pt/admin/certificates/certificatetemplate/2/change/ with content [lms_certificate_template.html](lms_certificate_template.html).

Run development server as:

```bash
FLASK_ENV=development flask run
```

To run the application on production you should use the uwsgi server. Run it like:

```bash
uwsgi uwsgi.ini
```

## Docker

Build image
```bash
docker-compose build
```

Run
```bash
docker-compose up
```

# NAU Course Certificate

This repository contains the source code of the NAU Course Certificate application. 
This should be installed as a docker container.

For development proposes you can run using flask (recomended), uwsgi or uwsgi inside of a docker container.

Prepare:

```bash
virtualenv venv --python=python3
source venv/bin/activate
python -m pip install -r requirements.txt --upgrade
```

Run development server as:

```bash
FLASK_ENV=development flask run
```

Alternatively using uwsgi:

```bash
uwsgi uwsgi.ini
```

Using docker:

```bash
docker-compose build && docker-compose up
```

## DEV
Change the certificate template on openedx LMS on https://lms.dev.nau.fccn.pt/admin/certificates/certificatetemplate/2/change/ with content [nau_base_certificate.mako](nau_base_certificate.mako).

TODO....

## STAGE

Change the certificate template on openedx LMS on https://lms.stage.nau.fccn.pt/admin/certificates/certificatetemplate/35/change/ with content [nau_base_certificate.mako](nau_base_certificate.mako).

Verify if the certificate is ok on the preview: https://lms.stage.nau.fccn.pt/certificates/user/367/course/course-v1:CNCS+CC101+2018_T1?preview=honor

Delete previous cached certificate.
```bash
AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXX AWS_SECRET_ACCESS_KEY=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY s3cmd --host 10.0.12.62 --host-bucket nau-stage-certificates --no-ssl rm -rf "s3://nau-stage-certificates/certificates/0f371aa73c8246d19bb784e819d5f806/"
```

View on local development server http://localhost:5000/inline/certificates/0f371aa73c8246d19bb784e819d5f806

View on STAGE https://lms.stage.nau.fccn.pt/certificates/0f371aa73c8246d19bb784e819d5f806

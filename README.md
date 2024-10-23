# NAU Course Certificate

This repository contains the source code of the NAU Course Certificate application. 
This should be installed as a docker container.

For development proposes you can run using flask (recomended), uwsgi or uwsgi inside of a docker container.

## Python
Tested using the Python version `3.11.8`.

## Virtual environment

```bash
virtualenv venv --python=python3
source venv/bin/activate
python -m pip install -r requirements.txt --upgrade
```

## Development server

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

## Local development

Change the certificate template on openedx LMS on https://lms.dev.nau.fccn.pt/admin/certificates/certificatetemplate/2/change/ with content [nau_base_certificate.mako](nau_base_certificate.mako). And change location of this app to localhost:5000 like is documented on template.

Open a certificate, like this: https://lms.dev.nau.fccn.pt/certificates/4d1d8ad2bcea43b7bac918ca328183b9
Click on "Print certificate" button or go to http://localhost:5000/attachment/certificates/4d1d8ad2bcea43b7bac918ca328183b9

After each download delete the generated file for next test:
```bash
AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXX AWS_SECRET_ACCESS_KEY=YYYYYYYYYYYYYYYYYYYYYYYYYYY s3cmd --host 10.0.12.62 --host-bucket nau-development-certificates --no-ssl rm -rf "s3://nau-development-certificates/certificates/4d1d8ad2bcea43b7bac918ca328183b9/"
```

## Upgrade dependencies

On a virtual environment, install `pip-upgrader` and run it.
```
python -m pip install pip-upgrader
pip-upgrade
```

## Release

Create a new tag naming vx.x.x example v2.0.0.

```bash
git tag vx.x.x
git push --tags
```

The Github actions would update the latest docker image and generate multiple tags depending on the tag naming. Like "2", "2.0" and "2.0.0".

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


## Digital signature
To digital sign PDFs of course certificates it is need to have a certificate (public and key) to be used during the digital signature process.
For development proposes there is a digital signature that already is been created on folder `./digital_signature_dev`. With the following procedure:

Reference: https://deliciousbrains.com/ssl-certificate-authority-for-local-https-development/

Create certificate authority, when asked enter pass phrase for the CA key, like: "1234".
```bash
openssl genrsa -des3 -out NAU_DEV_CA.key 4096
```

Generate a root certificate, for 20 years. When asked enter pass phrase for the CA key, like: "1234".
```bash
openssl req -x509 -new -nodes -key NAU_DEV_CA.key -sha256 -days 7300 -out NAU_DEV_ROOT.pem
```

Insert this info when asked
  Country Name (2 letter code) [AU]:PT
  State or Province Name (full name) [Some-State]:Lisboa
  Locality Name (eg, city) []:Lisboa
  Organization Name (eg, company) [Internet Widgits Pty Ltd]:FCT
  Organizational Unit Name (eg, section) []:FCCN
  Common Name (e.g. server FQDN or YOUR name) []:NAU DEV Digital signature
  Email Address []:ajuda@nau.edu.pt

Creating CA-Signed Certificates:
Create private key
```bash
openssl genrsa -out sign-pdf.dev.nau.fccn.pt.key 4096
```

Create CSR:
```bash
openssl req -new -key sign-pdf.dev.nau.fccn.pt.key -out sign-pdf.dev.nau.fccn.pt.csr -subj "/C=PT/ST=Lisboa/L=Lisboa/O=Fundação para a Ciência e a Tecnologia/OU=FCT/CN=sign-pdf.dev.nau.fccn.pt"
```

Create file sign-pdf.dev.nau.fccn.pt.ext
```bash
echo \
"
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = dev.nau.fccn.pt
" > sign-pdf.dev.nau.fccn.pt.ext
```

Create the certificate for 5 years
```bash
openssl x509 -req -in sign-pdf.dev.nau.fccn.pt.csr -CA NAU_DEV_ROOT.pem -CAkey NAU_DEV_CA.key -CAcreateserial -out sign-pdf.dev.nau.fccn.pt.crt -days 1825 -sha256 -extfile sign-pdf.dev.nau.fccn.pt.ext
```

Generate .p12 file with private key, public certificate and root public certificate. 
Insert a new password: 1234
```bash
openssl pkcs12 -export -out sign-pdf.dev.nau.fccn.pt.p12 -inkey sign-pdf.dev.nau.fccn.pt.key -in sign-pdf.dev.nau.fccn.pt.crt -certfile NAU_DEV_ROOT.pem
```

## STAGE

Delete old print of certificate and then download it a new one on pt-pt language.

```bash
AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXX AWS_SECRET_ACCESS_KEY=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY s3cmd --host 10.0.12.62 --host-bucket nau-stage-certificates --no-ssl rm -rf "s3://nau-stage-certificates/certificates/8f7276c174194d36bc5063d90967b766/"

curl -v https://course-certificate.stage.nau.fccn.pt/attachment/certificates/8f7276c174194d36bc5063d90967b766?language=pt-pt --output nau_stage_course_certificate_example.pdf
```

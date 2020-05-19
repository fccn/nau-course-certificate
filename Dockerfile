FROM python:3-alpine

# install uwsgi
RUN apk add --virtual .build-dependencies \
            --no-cache \
            python3-dev \
            build-base \
            linux-headers \
            pcre-dev
RUN apk add --no-cache pcre

# dependencies of this app
RUN apk add --no-cache wkhtmltopdf

WORKDIR /app
COPY . .
COPY requirements.txt .
RUN pip install -r requirements.txt

# clean python3 dev
RUN apk del .build-dependencies && rm -rf /var/cache/apk/*

# Expose the port
EXPOSE 5000

# Startup uwsgi
CMD ["uwsgi", "--ini", "uwsgi.ini"]

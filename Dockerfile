# Docker image for the nau-course-certificate application.
# It uses wkhtmltopdf package from maintainers instead of repository version.
# Because we are using features that are only available on the patched qt version of wkhtmltopdf.
# It is based on ubuntu image because the wkhtmltopdf deb depends on 'libjpeg-turbo8' package that was removed from the debian repositories.
# In future we hope that wkhtmltopdf maintainer review the code and its dependencies.
FROM ubuntu:20.04
LABEL maintainer="ivo.branco@fccn.pt"

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get upgrade -y

# Download and install wkhtmltopdf
RUN apt-get install -y build-essential xorg libssl-dev libxrender-dev wget

# Install wkhtmltopdf dependencies
RUN apt-get update && apt-get install -y --no-install-recommends xvfb libfontconfig libjpeg-turbo8 xfonts-75dpi fontconfig

# Download and install wkhtmltopdf from maintainers page so we include a version with a patched qt and include support for more features.
RUN wget --quiet https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
RUN dpkg -i wkhtmltox_0.12.6-1.bionic_amd64.deb
RUN rm wkhtmltox_0.12.6-1.bionic_amd64.deb

# Install swig debian package for pip requirement endesive
RUN apt-get install -y swig

# Install python3 and pip
RUN apt-get install -y python3.9 python3-pip

# Cleanup apt cache
RUN apt-get -y clean && \
    apt-get -y purge && \
    rm -rf /var/lib/apt/lists/* /tmp/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

COPY app.py uwsgi.ini ./
COPY static static
COPY nau nau

# Expose the port
EXPOSE 5000

# Startup uwsgi
CMD ["uwsgi", "--ini", "uwsgi.ini"]

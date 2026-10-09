# Docker image for the nau-course-certificate application.
# It uses Playwright with a bundled Chromium browser to render certificates
# to PDF/PNG (see https://github.com/fccn/nau-technical/issues/879).
# It previously used wkhtmltopdf, which is now archived and unmaintained.
FROM ubuntu:24.04
LABEL maintainer="info@nau.edu.pt"

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y build-essential

# Install swig debian package for pip requirement endesive
RUN apt-get install -y swig

RUN apt-get install -y libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git

ARG PYTHON_VERSION=3.11.8
ENV PYENV_ROOT /opt/pyenv
RUN git clone https://github.com/pyenv/pyenv $PYENV_ROOT --branch v2.3.36 --depth 1

# Install Python
RUN $PYENV_ROOT/bin/pyenv install $PYTHON_VERSION

# Create virtualenv
RUN $PYENV_ROOT/versions/$PYTHON_VERSION/bin/python -m venv /opt/venv

# Create virtual environment
RUN python3 -m venv /opt/venv

# Activate virtual environment
ENV PATH /opt/venv/bin:${PATH}
ENV VIRTUAL_ENV /opt/venv/

WORKDIR /app

RUN pip install \
    # https://pypi.org/project/setuptools/
    # https://pypi.org/project/pip/
    # https://pypi.org/project/wheel/
    setuptools==69.1.1 pip==24.0 wheel==0.43.0

# Install requirements file
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# Install the Chromium browser and its OS-level dependencies used by
# Playwright to render certificates to PDF/PNG.
RUN python -m playwright install --with-deps chromium

# Cleanup apt cache
RUN apt-get -y clean && \
    apt-get -y purge && \
    rm -rf /var/lib/apt/lists/* /tmp/*

# Default amount of uWSGI processes
ENV UWSGI_WORKERS=2

COPY app.py uwsgi.ini default-config.yml ./
COPY static static
COPY nau nau

# Expose the port
EXPOSE 5000

# Startup uwsgi
CMD ["uwsgi", "--ini", "uwsgi.ini"]

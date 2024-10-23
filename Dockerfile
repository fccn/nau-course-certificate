# Docker image for the nau-course-certificate application.
# It uses wkhtmltopdf package from maintainers instead of repository version.
# Because we are using features that are only available on the patched qt version of wkhtmltopdf.
# It is based on ubuntu image because the wkhtmltopdf deb depends on 'libjpeg-turbo8' package that was removed from the debian repositories.
# In future we hope that wkhtmltopdf maintainer review the code and its dependencies.
FROM ubuntu:24.04
LABEL maintainer="info@nau.edu.pt"

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get upgrade -y

# Download and install wkhtmltopdf
RUN apt-get install -y build-essential xorg libssl-dev libxrender-dev wget

# Install wkhtmltopdf dependencies
RUN apt-get install -y --no-install-recommends xvfb libfontconfig libjpeg-turbo8 xfonts-75dpi fontconfig

# Download and install wkhtmltopdf from maintainers page so we include a version with a patched qt and include support for more features.
RUN wget --quiet https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
RUN dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb
RUN rm wkhtmltox_0.12.6.1-2.jammy_amd64.deb

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

# Cleanup apt cache
RUN apt-get -y clean && \
    apt-get -y purge && \
    rm -rf /var/lib/apt/lists/* /tmp/*

WORKDIR /app

RUN pip install \
    # https://pypi.org/project/setuptools/
    # https://pypi.org/project/pip/
    # https://pypi.org/project/wheel/
    setuptools==69.1.1 pip==24.0 wheel==0.43.0

# Install requirements file
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY app.py uwsgi.ini default-config.yml ./
COPY static static
COPY nau nau

# Expose the port
EXPOSE 5000

# Startup uwsgi
CMD ["uwsgi", "--ini", "uwsgi.ini"]

# FROM 310830963532.dkr.ecr.eu-central-1.amazonaws.com/ta3leem-openedx:base
FROM registry.creativeadvtech.com/ta3leem/openedx:base

# Command to run static files generation, should be run on production to initialize/update static files
# mysql:
# SET global innodb_file_format = BARRACUDA;
# SET global innodb_large_prefix = ON;
# CREATE DATABASE edxapp CHARACTER SET utf8 COLLATE utf8_general_ci;
# CREATE DATABASE edxapp_csmh CHARACTER SET utf8 COLLATE utf8_general_ci;
# cms/lms:
# python3 manage.py cms migrate --settings=production
# python3 manage.py lms migrate --settings=production
# cms/lms assets:
# npm install -g rtlcss && DJANGO_SETTINGS_MODULE="" paver update_assets --debug-collect --settings production --themes taleem-theme lms
# npm install -g rtlcss && DJANGO_SETTINGS_MODULE="" paver update_assets --debug-collect --settings production --themes taleem-theme cms

# Maintainers
LABEL MAINTAINER="pkalinowski@creativeadvtech.com"
LABEL MAINTAINER="apandili@creativeadvtech.com"

RUN apt-get update && \
    apt-get install unzip -y && \
    curl https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/bin/mc && \
    chmod +x /usr/bin/mc

# Hack supervisorctl
RUN sed -i '1 i\#!/usr/bin/python2.7' /usr/bin/supervisorctl
RUN pip2 install supervisor==3.3.1

# Make alternative
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 10
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Static assets
RUN mkdir /openedx /openedx/data /openedx/edx-platform
WORKDIR /openedx/edx-platform

COPY ./ /openedx/edx-platform

# Requirements
RUN pip3 install -r requirements/edx/base.txt
RUN pip3 install -r requirements/edx/development.txt

RUN npm install

# Static generation
ENV BUILD true

ENV STUDIO_CFG /openedx/edx-platform/config/cms.yml
ENV LMS_CFG /openedx/edx-platform/config/lms.yml
ENV LANG en_US.UTF-8
ENV SETTINGS production
ENV NO_PREREQ_INSTALL "1"
ENV SETUPTOOLS_USE_DISTUTILS stdlib
ENV SKIP_WS_MIGRATIONS "1"
ENV REVISION_CFG /openedx/edx-platform/config/revisions.yml

RUN npm install -g rtlcss yuglify cssmin
RUN paver update_assets --debug-collect --settings production

RUN cp -R /openedx/edx-platform/static/js /openedx/edx-platform/static/studio
RUN cp -R /openedx/edx-platform/static/bundles /openedx/edx-platform/static/studio

ENV BUILD false

# Copy convenient scripts
COPY ./bin /openedx/bin
RUN chmod a+x /openedx/bin/*
ENV PATH /openedx/bin:${PATH}

# Service variant is "lms" or "cms"
ENV SERVICE_VARIANT lms
ENV SETTINGS production

# Entrypoint will fix permissiosn of all files and run commands as openedx
ENTRYPOINT ["docker-entrypoint.sh"]

# Run server
EXPOSE 8000
CMD python2 /usr/bin/supervisord

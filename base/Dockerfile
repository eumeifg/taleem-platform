FROM ubuntu:18.04

# Install python requirements
ENV NO_PYTHON_UNINSTALL 1
ENV LC_ALL en_US.UTF-8

# Install system requirements
RUN apt update && \
  apt upgrade -y && \
  # Global requirements
  DEBIAN_FRONTEND="noninteractive" apt install -y language-pack-en git  build-essential software-properties-common curl git-core libxml2-dev libxslt1-dev python3-pip python-pip libmysqlclient-dev python3-apt python3-dev libxmlsec1-dev libfreetype6-dev swig gcc g++ && \
  # openedx requirements
  DEBIAN_FRONTEND="noninteractive" apt install -y gettext gfortran graphviz graphviz-dev libffi-dev libfreetype6-dev libgeos-dev libjpeg8-dev liblapack-dev libpng-dev libsqlite3-dev libxml2-dev libxmlsec1-dev libxslt1-dev ntp pkg-config && \
  # Our requirements
  DEBIAN_FRONTEND="noninteractive" apt install -y mysql-client && \
  DEBIAN_FRONTEND="noninteractive" apt install -y nginx supervisor

# Stop nginx service
RUN service nginx stop && rm -rf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

#RUN rm /etc/nginx/conf.d/default.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf


# Install nodejs requirements
RUN curl -sL https://deb.nodesource.com/setup_11.x  | bash -
RUN apt-get -y install nodejs

# Dockerize
ENV DOCKERIZE_VERSION v0.6.1
RUN curl -L -o dockerize.tar.gz https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize.tar.gz \
    && rm dockerize.tar.gz
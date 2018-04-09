FROM alpine:3.7
MAINTAINER Xiepeng Li <phiedulxp@gmail.com>
ENV LANG C.UTF-8

RUN { \
    echo '#!/bin/sh'; \
    echo 'set -e'; \
    echo; \
    echo 'dirname "$(dirname "$(readlink -f "$(which javac || which java)")")"'; \
  } > /usr/local/bin/docker-java-home \
  && chmod +x /usr/local/bin/docker-java-home
ENV JAVA_HOME /usr/lib/jvm/java-1.8-openjdk
ENV PATH $PATH:/usr/lib/jvm/java-1.8-openjdk/jre/bin:/usr/lib/jvm/java-1.8-openjdk/bin

ENV JAVA_VERSION 8u111
ENV JAVA_ALPINE_VERSION 8.111.14-r0

RUN set -x \
  && apk add --no-cache \
    openjdk8="$JAVA_ALPINE_VERSION" \
  && [ "$JAVA_HOME" = "$(docker-java-home)" ]
  
RUN apk add --update \
    python \
    python-dev \
    py-pip \
    build-base \
  && pip install virtualenv \
  && rm -rf /var/cache/apk/*

ADD . /PKUSUMSUM-docker

ADD lib/liblpsolve55.so /usr/local/lib
ADD lib/liblpsolve55j.so /usr/local/lib

RUN /sbin/ldconfig

WORKDIR /PKUSUMSUM-docker

RUN pip install -r requirements.txt

EXPOSE 8080
# dash app
CMD ['/env/bin/python','server-dash.py']
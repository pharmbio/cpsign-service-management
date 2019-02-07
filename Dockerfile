FROM python:3.5.6-slim

# Set pachctl version to match desired pachd version
ARG pachctl_version=1.7.10

RUN apt update && apt install -y --no-install-recommends nano mysql-client apt-transport-https ca-certificates gnupg curl && \
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list && \
    curl -o /tmp/pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v${pachctl_version}/pachctl_${pachctl_version}_amd64.deb && dpkg -i /tmp/pachctl.deb && \
    apt update && apt install -y --no-install-recommends kubectl  && \
    pip3.5 install pymysql jinja2 && rm /tmp/pachctl.deb

ADD examples/params.txt /home/example
ADD README.md /home/
ADD LogD /home/LogD
ADD configuration.json /home/configuration.json

WORKDIR /home


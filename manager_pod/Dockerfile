FROM python:3.5.6-slim

# Set pachctl version to match desired pachd version
ARG pachctl_version=1.7.10


RUN apt update && apt install -y --no-install-recommends apt-transport-https ca-certificates gnupg curl && \
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list && \
    apt update && apt install -y --no-install-recommends kubectl && \
    curl -o /tmp/pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v${pachctl_version}/pachctl_${pachctl_version}_amd64.deb && dpkg -i /tmp/pachctl.deb && \
    pip3.5 install pymysql python_pachyderm && rm /tmp/pachctl.deb

ADD params.txt /home/
ADD spec-train.json /home/cpsign-setup/
ADD data_ingestion.py /home/
ADD README.md /home/


WORKDIR /home
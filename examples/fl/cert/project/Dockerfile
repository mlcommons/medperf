FROM python:3.11.9-alpine

# update openssl to fix https://avd.aquasec.com/nvd/cve-2024-2511 
RUN apk update && apk add openssl=3.1.4-r6 jq

ARG VERSION=0.26.1
RUN wget https://dl.smallstep.com/gh-release/cli/gh-release-header/v${VERSION}/step_linux_${VERSION}_amd64.tar.gz \
    && tar -xf step_linux_${VERSION}_amd64.tar.gz \
    && cp step_${VERSION}/bin/step /usr/bin

COPY . /mlcube_project

ENTRYPOINT ["/bin/sh"]
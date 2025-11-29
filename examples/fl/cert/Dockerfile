FROM python:3.11.9-alpine

RUN apk update && apk add jq curl

ARG VERSION=0.26.1
RUN wget https://dl.smallstep.com/gh-release/cli/gh-release-header/v${VERSION}/step_linux_${VERSION}_amd64.tar.gz \
    && tar -xf step_linux_${VERSION}_amd64.tar.gz \
    && cp step_${VERSION}/bin/step /usr/bin

COPY project /project

ENTRYPOINT ["/bin/sh"]
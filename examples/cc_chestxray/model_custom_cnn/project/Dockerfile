FROM python:3.9.16-slim

RUN apt-get update && apt-get install curl jq -y

COPY ./requirements.txt /mlcube_project/requirements.txt 

RUN pip3 install --no-cache-dir -r /mlcube_project/requirements.txt

COPY --from=hasan7/coco-kbs-client:0.0.0 /usr/local/bin/kbs-client /usr/local/bin/kbs-client

ENV LANG C.UTF-8

COPY . /mlcube_project

ENTRYPOINT ["/usr/bin/bash", "/mlcube_project/entrypoint.sh"]
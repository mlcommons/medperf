FROM python:3.9.16-slim

COPY ./requirements.txt /mlcube_project/requirements.txt 

RUN pip3 install -r /mlcube_project/requirements.txt

ENV LANG C.UTF-8

COPY . /mlcube_project

ENTRYPOINT ["python3", "/mlcube_project/mlcube.py"]
FROM python:3.9.16-slim

COPY ./requirements.txt /project/requirements.txt 

RUN pip3 install --no-cache-dir -r /project/requirements.txt

ENV LANG C.UTF-8

COPY . /project

ENTRYPOINT ["python3", "/project/mlcube.py"]

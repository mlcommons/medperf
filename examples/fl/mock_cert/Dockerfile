FROM python:3.9.16-slim

COPY project/requirements.txt /project/requirements.txt 

RUN pip3 install --no-cache-dir -r /project/requirements.txt

ENV LANG C.UTF-8

COPY project /project

RUN chmod a+r /project/ca/root.key

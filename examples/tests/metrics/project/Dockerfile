FROM python:3.8.13-slim
LABEL org.opencontainers.image.authors="Hasan"


COPY ./requirements.txt project/requirements.txt 

ENV LANG C.UTF-8

RUN pip3 install --no-cache-dir -r project/requirements.txt

COPY . /project

WORKDIR /project

ENTRYPOINT ["python3", "/project/metrics.py"]

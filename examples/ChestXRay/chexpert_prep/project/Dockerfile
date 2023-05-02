FROM ubuntu:18.04
MAINTAINER MLPerf MLBox Working Group

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	software-properties-common \
	python3-dev \
	curl && \
	rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:deadsnakes/ppa -y && apt-get update

RUN apt-get install python3 -y

RUN curl -fSsL -O https://bootstrap.pypa.io/pip/3.6/get-pip.py && \
	python3 get-pip.py && \
	rm get-pip.py

COPY ./requirements.txt project/requirements.txt 

RUN pip3 install --upgrade pip

RUN pip3 install --no-cache-dir -r project/requirements.txt

ENV LANG C.UTF-8

COPY . /project

WORKDIR /project

ENTRYPOINT ["python3", "/project/mlcube.py"]
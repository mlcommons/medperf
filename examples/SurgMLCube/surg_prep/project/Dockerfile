FROM ubuntu:18.04
LABEL org.opencontainers.image.authors="MLPerf MLBox Working Group"

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	software-properties-common \
	python3-dev \
	curl && \
	rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:deadsnakes/ppa -y && apt-get update

RUN apt-get install python3 -y

RUN apt-get install python3-pip -y

COPY ./requirements.txt project/requirements.txt 

RUN pip3 install --upgrade pip

RUN pip3 install --no-cache-dir -r project/requirements.txt

RUN apt-get install ffmpeg -y

ENV LANG C.UTF-8

COPY ./requirements.txt project/requirements.txt 

RUN pip3 install --no-cache-dir -r project/requirements.txt

COPY . /project

WORKDIR /project

ENTRYPOINT ["python3", "mlcube.py"]

FROM pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime
MAINTAINER MLPerf MLBox Working Group

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    ffmpeg libsm6 libxext6 \
    python3-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:deadsnakes/ppa -y && apt-get update

RUN apt-get install libglu1 libglew-dev -y

RUN apt-get install python3 -y

RUN apt-get install -y --no-install-recommends \ 
    python3.6 \
    python3.6-venv \
    python3.6-dev \
    python3-setuptools \
    wget \
    zip \
    unzip

RUN apt-get install python3-pip -y

ARG FETS_VERSION=0.0.7

RUN wget https://fets.projects.nitrc.org/FeTS_${FETS_VERSION}_Installer.bin && chmod +x ./FeTS_*_Installer.bin

RUN yes | ./FeTS_${FETS_VERSION}_Installer.bin --target /usr/local/fets_installation

ENV LD_LIBRARY_PATH=/usr/local/fets_installation/squashfs-root/usr/lib:$LD_LIBRARY_PATH

ENV PATH=/usr/local/fets_installation/squashfs-root/usr/bin:$PATH

ENV LANG C.UTF-8

COPY . /project

WORKDIR /project

RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "mlcube.py"]

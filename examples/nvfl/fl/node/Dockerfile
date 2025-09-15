FROM python:3.10
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends zip git zlib1g-dev libffi-dev libgl1 libgtk2.0-dev gcc g++

RUN pip install -U pip
RUN pip install nvflare==2.6

# ########################

COPY project/requirements.txt /project/requirements.txt
RUN pip install --no-cache-dir -r /project/requirements.txt

# Copy mlcube workspace
COPY project /project


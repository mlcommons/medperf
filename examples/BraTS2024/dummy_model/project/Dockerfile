FROM python:3.9.16-slim

COPY ./requirements.txt /mlcube_project/requirements.txt 

RUN pip3 install --no-cache-dir -r /mlcube_project/requirements.txt

ENV LANG C.UTF-8

# Create a non-root user.
RUN useradd nonrootuser
USER nonrootuser

COPY . /mlcube_project

ENTRYPOINT ["python3", "/mlcube_project/mlcube.py"]
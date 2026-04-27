FROM flwr/base:1.25.0-py3.13-ubuntu24.04

COPY project/requirements.txt /project/requirements.txt
RUN pip install --no-cache-dir -r /project/requirements.txt

COPY project /project
ENV FLWR_HOME=/tmp

ENTRYPOINT ["python", "/project/entrypoint.py"]
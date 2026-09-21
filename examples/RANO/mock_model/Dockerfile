# Build context is examples/RANO/mock_model/:
#   docker build -t <your-dockerhub-user>/rano-mock-model:0.0.1 examples/RANO/mock_model
FROM python:3.10-slim
ENV LANG=C.UTF-8

COPY project/requirements.txt /project/requirements.txt
RUN pip3 install --no-cache-dir -r /project/requirements.txt

COPY project /project
ENTRYPOINT []

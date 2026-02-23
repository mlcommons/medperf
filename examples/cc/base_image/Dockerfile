FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /project/requirements.txt 

RUN pip3 install --no-cache-dir -r /project/requirements.txt

ENV LANG C.UTF-8

COPY ./src /project/

ENTRYPOINT ["bash", "/project/entrypoint.sh"]

CMD []

# Allow the workload to access the following environment variables
LABEL "tee.launch_policy.allow_env_override"="DATA_CONFIG,EXPECTED_DATA_HASH,MODEL_CONFIG,EXPECTED_MODEL_HASH,RESULT_CONFIG,RESULT_COLLECTOR,EXPECTED_RESULT_COLLECTOR_HASH"
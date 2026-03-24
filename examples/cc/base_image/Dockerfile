FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3.12 -m venv /opt/medperf-venv

# Activate venv by default
ENV PATH="/opt/medperf-venv/bin:$PATH"

ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /project/requirements.txt 

RUN pip3 install --no-cache-dir -r /project/requirements.txt

COPY ./src /project/

ENTRYPOINT ["bash", "/project/entrypoint.sh"]

CMD []

# Allow the workload to access the following environment variables
LABEL "tee.launch_policy.allow_env_override"="DATA_CONFIG,EXPECTED_DATA_HASH,MODEL_CONFIG,EXPECTED_MODEL_HASH,RESULT_CONFIG,RESULT_COLLECTOR,EXPECTED_RESULT_COLLECTOR_HASH"
LABEL "tee.launch_policy.log_redirect"="always"
FROM ubuntu:22.04


RUN apt-get clean && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install --no-install-recommends --fix-missing -y \
    curl \
    gpg-agent \
    software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --fix-missing -y \
    python3.12 \
    python3.12-venv && \
    python3.12 -m ensurepip --upgrade && \
    python3.12 -m pip install --upgrade pip setuptools && \
    apt-get purge -y \
    curl \
    gpg-agent \
    software-properties-common && \
    apt-get autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/local/bin/pip3.12 /usr/local/bin/pip && \
    ln -sf /usr/local/bin/pip3.12 /usr/local/bin/pip3

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
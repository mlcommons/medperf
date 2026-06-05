FROM mlcommons/medperf-confidential-benchmark-base:0.0.0

COPY ./requirements.txt /project/requirements.txt 

RUN pip3 install --no-cache-dir -r /project/requirements.txt

COPY ./benchmark /project/benchmark
FROM mlcommons/medperf-confidential-benchmark-base:0.0.1

COPY ./requirements.txt /project/requirements.txt
COPY ./benchmark/sut_loader/requirements.txt /project/benchmark/sut_loader/requirements.txt

# Torch defaults to the CUDA build, which is right for a GPU enclave and several
# wasted gigabytes on a machine without one. Point this at
# https://download.pytorch.org/whl/cpu to build a CPU-only image.
ARG TORCH_INDEX_URL=""
RUN if [ -n "$TORCH_INDEX_URL" ]; then \
        pip3 install --no-cache-dir --index-url "$TORCH_INDEX_URL" torch; \
    fi

RUN pip3 install --no-cache-dir \
    -r /project/requirements.txt \
    -r /project/benchmark/sut_loader/requirements.txt

COPY ./benchmark /project/benchmark

RUN chmod +x /project/benchmark/entrypoint.sh \
             /project/benchmark/sut_loader/run.sh

# The model under test is decrypted onto disk beside this container; nothing it
# serves is fetched from HuggingFace.
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

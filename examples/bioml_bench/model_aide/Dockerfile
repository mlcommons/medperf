# BioML-bench's AIDE agent (agents/aide), with the LLM served by vLLM in the
# same container, so the agent runs without network access.
#
# Build from examples/bioml_bench (see build.sh):
#   docker buildx build --platform linux/arm64 -f model_aide/Dockerfile --push -t <image> .
#
# The agent gets its own Python, separate from vLLM's, so neither can break the
# other's packages. It is installed on the build machine for the target
# platform (wheels only, except pure Python packages) and copied onto the vLLM
# image. Nothing runs on the vLLM image, so the build neither emulates arm64
# nor needs the vLLM image (about 12 GB) on disk: with --push, its layers stay
# in the registry.
ARG VLLM_IMAGE=vllm/vllm-openai:v0.31.0-cu129

FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:0.8.22-python3.12-bookworm-slim AS agent

ARG TARGETARCH
# slow links time out with uv's default of 30 s
ENV UV_HTTP_TIMEOUT=300
# downloads are kept in a build cache (see the RUN below), outside the image
ENV UV_LINK_MODE=copy
# github.com/AIxBio/aideml_bmlb, the AIDE fork BioML-bench installs
ARG AIDE_COMMIT=c261d4a276dd76abac303e9a9d344b290b3266d8

COPY model_aide/project/requirements.txt /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.cache/uv \
    ARCH="$([ "$TARGETARCH" = arm64 ] && echo aarch64 || echo x86_64)" \
    && uv python install --install-dir /tmp/python "cpython-3.12-linux-$ARCH-gnu" \
    && mkdir /opt/agent \
    && mv /tmp/python/cpython-3.12.*-linux-$ARCH-gnu /opt/agent/python \
    && INSTALL="uv pip install --target /opt/agent/python/lib/python3.12/site-packages --python-version 3.12 --python-platform $ARCH-manylinux_2_28 --exclude-newer 2025-09-01" \
    && $INSTALL -r /tmp/requirements.txt \
        --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match \
        --only-binary :all: --no-binary antlr4-python3-runtime \
    && $INSTALL --no-deps "aideml @ https://github.com/AIxBio/aideml_bmlb/archive/${AIDE_COMMIT}.tar.gz"

COPY common/check_platform.py /tmp/
RUN python3 /tmp/check_platform.py /opt/agent "$TARGETARCH"

FROM ${VLLM_IMAGE}

COPY --link --from=agent /opt/agent /opt/agent
COPY --link model_aide/project /project

ENTRYPOINT ["/opt/agent/python/bin/python3", "/project/infer.py"]

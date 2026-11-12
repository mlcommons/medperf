# Build from examples/bioml_bench (see build.sh):
#   docker buildx build --platform linux/arm64 -f data_preparator/Dockerfile .
#
# The Python packages are installed on the build machine, for the target
# platform, then copied onto the target image. An arm64 image therefore builds
# on an x86 machine without emulation. Only wheels are installed, as a package
# built from source here would be built for the build machine's CPU; the
# exceptions are pure Python (asciitree, and BioML-bench itself).
FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:0.8.22-python3.11-bookworm-slim AS packages

ARG TARGETARCH
# slow links time out with uv's default of 30 s
ENV UV_HTTP_TIMEOUT=300
# downloads are kept in a build cache (see the RUN below), outside the image
ENV UV_LINK_MODE=copy
ARG BIOMLBENCH_COMMIT=673f3d8d3462fc6cdcbbd9695fba612b9332ca65
# numcodecs 0.15, which polaris requires, has no Linux arm64 wheel: conda-forge's
# arm64 build of it is installed instead (see common/overrides.txt)
ARG NUMCODECS_ARM64=https://conda.anaconda.org/conda-forge/linux-aarch64/numcodecs-0.15.1-py311h848c333_0.conda
ARG NUMCODECS_ARM64_SHA256=70302867507e921f390ad3f7b317e223bb76e233508fa452c524f0e3ea94baf9

COPY common/requirements.txt common/overrides.txt common/check_platform.py common/install_conda_package.py /tmp/

RUN --mount=type=cache,target=/root/.cache/uv \
    PLATFORM="$([ "$TARGETARCH" = arm64 ] && echo aarch64 || echo x86_64)-manylinux_2_28" \
    && INSTALL="uv pip install --target /opt/site-packages --python-version 3.11 --python-platform $PLATFORM --exclude-newer 2025-09-01" \
    && $INSTALL -r /tmp/requirements.txt --override /tmp/overrides.txt \
        --only-binary :all: --no-binary asciitree \
    && $INSTALL --no-deps "bioml-bench @ https://github.com/science-machine/biomlbench/archive/${BIOMLBENCH_COMMIT}.tar.gz" \
    && if [ "$TARGETARCH" = arm64 ]; then \
        uv run --no-project --with zstandard==0.23.0 python3 /tmp/install_conda_package.py \
            "$NUMCODECS_ARM64" "$NUMCODECS_ARM64_SHA256" /opt/site-packages; fi \
    && python3 /tmp/check_platform.py /opt/site-packages "$TARGETARCH"

FROM python:3.11-slim-bookworm

COPY --link --from=packages /opt/site-packages /usr/local/lib/python3.11/site-packages
COPY --link common/fastpdb /usr/local/lib/python3.11/site-packages/fastpdb

ENV LANG=C.UTF-8
ENV HOME=/tmp
WORKDIR /tmp

COPY common/biomlbench_task.py /project/
COPY data_preparator/project /project

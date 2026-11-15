# Build from examples/bioml_bench (see build.sh):
#   docker buildx build --platform linux/arm64 -f model_dummy/Dockerfile .
FROM python:3.11-slim-bookworm

ENV LANG=C.UTF-8

COPY model_dummy/project /project

ENTRYPOINT ["python3", "/project/infer.py"]

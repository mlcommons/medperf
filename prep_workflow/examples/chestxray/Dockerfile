# Build context is examples/prep_workflow/:
#   docker build -f examples/chestxray/Dockerfile -t mlcommons/chestxray-prep-workflow:0.1.0 .
FROM python:3.9-slim
ENV LANG=C.UTF-8

COPY pyproject.toml /orchestrator/pyproject.toml
COPY prep_workflow /orchestrator/prep_workflow
RUN pip3 install --no-cache-dir /orchestrator

COPY examples/chestxray/project/requirements.txt /project/requirements.txt
RUN pip3 install --no-cache-dir -r /project/requirements.txt

COPY examples/chestxray/project /project
ENV PROJECT_DIR=/project WORKFLOW_YAML=/project/workflow.yaml

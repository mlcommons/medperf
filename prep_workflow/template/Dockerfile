# Build context is examples/prep_workflow/ (so the orchestrator package is visible).
#   docker build -f template/Dockerfile -t my-org/my-data-prep:0.0.1 .
FROM python:3.9-slim

ENV LANG=C.UTF-8

# Install the workflow orchestrator (provided; authors don't edit it).
COPY pyproject.toml /orchestrator/pyproject.toml
COPY prep_workflow /orchestrator/prep_workflow
RUN pip3 install --no-cache-dir /orchestrator

# Install the author's step/condition dependencies.
COPY template/project/requirements.txt /project/requirements.txt
RUN pip3 install --no-cache-dir -r /project/requirements.txt

# Bake in the author's steps, conditions and workflow graph.
COPY template/project /project

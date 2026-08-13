# Build context is examples/prep_workflow/ so both the orchestrator package and
# this example's project are visible:
#   docker build -f examples/rano/Dockerfile -t mlcommons/rano-data-prep-workflow:0.1.0 .
#
# The scientific code (nnU-Net models, DICOM/NIfTI tooling, stages/constants.py)
# comes from the RANO base image; we overlay the reused stages + the orchestrator.

# this prebuilt image is based on code from alejandro's branch.
FROM mlcommons/rano-data-prep-mlcube:1.0.10

RUN /bin/sh -c sed -i '36s|.*|    temp_path = Path("/tmp") / ".report.yaml"|' /project/stages/pipeline.py # buildkit
RUN /bin/sh -c sed -i '39s|.*|    shutil.move(temp_path, filepath)|' /project/stages/pipeline.py # buildkit
RUN /bin/sh -c sed -i '1i import shutil' /project/stages/pipeline.py # buildkit

# The workflow orchestrator (provided; authors don't edit it).
COPY pyproject.toml /orchestrator/pyproject.toml
COPY prep_workflow /orchestrator/prep_workflow
RUN pip3 install --no-cache-dir /orchestrator

# Overlay the reused RANO stages + our steps/conditions/workflow onto the base
# image's /project (which supplies stages/constants.py and the heavy libraries).
COPY examples/rano/project /project
RUN pip3 install --no-cache-dir -r /project/requirements.txt

# The reused stages expect a /workspace layout; MedPerf mounts are bound there
# (see container_config.yaml) and surfaced to the engine via these env vars.
ENV WORKSPACE_DIRECTORY=/workspace \
    PROJECT_DIR=/project \
    WORKFLOW_YAML=/project/workflow.yaml \
    INPUT_DATA=/workspace/input_data \
    INPUT_LABELS=/workspace/input_labels \
    OUTPUT_DATA=/workspace/data \
    OUTPUT_LABELS=/workspace/labels \
    METADATA=/workspace/metadata \
    ADDITIONAL_FILES=/workspace/additional_files \
    PARAMETERS_FILE=/workspace/parameters.yaml \
    REPORT_FILE=/workspace/report.yaml \
    STATISTICS_FILE=/workspace/statistics.yaml

# Reset the base image's entrypoint so the task command runs directly.
ENTRYPOINT []

# Build context is examples/prep_workflow/:
#   docker build -f examples/hemnet/Dockerfile -t mlcommons/hemnet-prep-workflow:0.1.0 .
FROM andrewsu1/hemnet:latest
RUN rm -rf /HEMnet && git clone -b master --single-branch --depth 1 \
    https://github.com/BiomedicalMachineLearning/HEMnet.git

# Reused HEMnet stage scripts into their working directory.
COPY examples/hemnet/project/science/*.py /HEMnet/HEMnet/

# Orchestrator into the HEMnet conda environment.
ENV PATH="/opt/conda/envs/HEMnet/bin:$PATH"
COPY pyproject.toml /orchestrator/pyproject.toml
COPY prep_workflow /orchestrator/prep_workflow
RUN pip install --no-cache-dir /orchestrator

COPY examples/hemnet/project /project
ENV WORKSPACE_DIRECTORY=/workspace \
    PROJECT_DIR=/project \
    WORKFLOW_YAML=/project/workflow.yaml \
    HEMNET_SCRIPTS=/HEMnet/HEMnet \
    INPUT_DATA=/workspace/input_data \
    INPUT_LABELS=/workspace/input_labels \
    OUTPUT_DATA=/workspace/data \
    OUTPUT_LABELS=/workspace/labels \
    METADATA=/workspace/metadata \
    ADDITIONAL_FILES=/workspace/additional_files \
    PARAMETERS_FILE=/workspace/parameters.yaml \
    REPORT_FILE=/workspace/report.yaml \
    STATISTICS_FILE=/workspace/statistics.yaml
ENTRYPOINT []

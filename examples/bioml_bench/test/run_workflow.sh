#!/bin/bash
# Runs the benchmark workflow on a task in tasks/, without a MedPerf server:
# prepare, sanity check, statistics, the Dummy model and the evaluation.
# Containers run as MedPerf runs them: as the host user, with read-only inputs
# and no network. The images are built for this machine's platform and tagged
# bioml-bench-<name>:local; rebuild them with REBUILD=1 after changing their code.
# Usage: bash run_workflow.sh <task folder> [workdir]
#   e.g. bash run_workflow.sh tasks/tdcommons-caco2-wang
set -euo pipefail

EXAMPLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_DIR="$(cd "${1:?Usage: bash run_workflow.sh <task folder> [workdir]}" && pwd)"
WORKDIR="${2:-$(mktemp -d)}"
PREP_IMAGE=bioml-bench-prep:local
METRICS_IMAGE=bioml-bench-metrics:local
DUMMY_IMAGE=bioml-bench-dummy:local

build() {
  if [ "${REBUILD:-0}" = 1 ] || ! docker image inspect "$1" > /dev/null 2>&1; then
    docker buildx build --builder default --load -t "$1" -f "$EXAMPLE_DIR/$2" "$EXAMPLE_DIR"
  fi
}
build "$PREP_IMAGE" data_preparator/Dockerfile
build "$METRICS_IMAGE" metrics/Dockerfile
build "$DUMMY_IMAGE" model_dummy/Dockerfile

run_container() {
  docker run --rm -u "$(id -u):$(id -g)" --network none "$@"
}

PARAMS=$TASK_DIR/parameters.yaml:/mlcommons/volumes/parameters/parameters_file.yaml:ro
mkdir -p "$WORKDIR"/{data,labels,predictions,results,statistics,additional_files}
touch "$WORKDIR/statistics/statistics.yaml" "$WORKDIR/results/results.yaml"
if [ -f "$TASK_DIR/metrics_additional_files.tar.gz" ]; then
  tar -xzf "$TASK_DIR/metrics_additional_files.tar.gz" -C "$WORKDIR/additional_files"
fi

run_container \
  -v "$TASK_DIR/raw/data:/mlcommons/volumes/raw_data:ro" \
  -v "$TASK_DIR/raw/labels:/mlcommons/volumes/raw_labels:ro" \
  -v "$PARAMS" \
  -v "$WORKDIR/data:/mlcommons/volumes/data:rw" \
  -v "$WORKDIR/labels:/mlcommons/volumes/labels:rw" \
  "$PREP_IMAGE" python3 /project/prepare.py

run_container \
  -v "$WORKDIR/data:/mlcommons/volumes/data:ro" \
  -v "$WORKDIR/labels:/mlcommons/volumes/labels:ro" \
  -v "$PARAMS" \
  "$PREP_IMAGE" python3 /project/sanity_check.py

run_container \
  -v "$WORKDIR/data:/mlcommons/volumes/data:ro" \
  -v "$WORKDIR/labels:/mlcommons/volumes/labels:ro" \
  -v "$PARAMS" \
  -v "$WORKDIR/statistics/statistics.yaml:/mlcommons/volumes/statistics/statistics.yaml:rw" \
  "$PREP_IMAGE" python3 /project/statistics.py

run_container \
  -v "$WORKDIR/data:/mlcommons/volumes/data:ro" \
  -v "$WORKDIR/predictions:/mlcommons/volumes/predictions:rw" \
  "$DUMMY_IMAGE"

run_container \
  -v "$WORKDIR/predictions:/mlcommons/volumes/predictions:ro" \
  -v "$WORKDIR/labels:/mlcommons/volumes/labels:ro" \
  -v "$PARAMS" \
  -v "$WORKDIR/additional_files:/mlcommons/volumes/additional_files:ro" \
  -v "$WORKDIR/results/results.yaml:/mlcommons/volumes/results/results.yaml:rw" \
  "$METRICS_IMAGE"

echo "--- workdir: $WORKDIR"
echo "--- prepared data:   $(ls "$WORKDIR/data" | tr '\n' ' ')"
echo "--- prepared labels: $(ls "$WORKDIR/labels" | tr '\n' ' ')"
echo "--- statistics"
cat "$WORKDIR/statistics/statistics.yaml"
echo "--- results"
cat "$WORKDIR/results/results.yaml"

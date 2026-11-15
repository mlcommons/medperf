#!/bin/bash
# Downloads a BioML-bench task into tasks/<task name>/: the raw dataset to
# register, the demo dataset, the leaderboard and the task's parameters. The
# tasks in tasks/ were made with this script; use it to add others.
#
# Usage: bash fetch_task.sh <task id> [image]
#   e.g. bash fetch_task.sh polarishub/tdcommons-caco2-wang
# The image is the data preparator's, which holds BioML-bench and the download
# code. Default: mhmdk0/bioml-bench-prep:0.0.1 (it must run on this machine:
# use an image built for its platform, e.g. bioml-bench-prep:local from
# test/run_workflow.sh).
set -euo pipefail

EXAMPLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_ID=${1:?"Usage: bash fetch_task.sh <task id> [image], e.g. polarishub/tdcommons-caco2-wang"}
IMAGE=${2:-mhmdk0/bioml-bench-prep:0.0.1}
OUT=$EXAMPLE_DIR/tasks/${TASK_ID#*/}

mkdir -p "$OUT"
docker run --rm -u "$(id -u):$(id -g)" -v "$OUT:/out:rw" "$IMAGE" \
  python3 /project/fetch.py --task "$TASK_ID" --out /out

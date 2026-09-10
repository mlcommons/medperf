#!/bin/bash
# Builds the safety benchmark script image and publishes it.
#
# MedPerf pulls whatever image a benchmark names, so a run executes the
# published tag rather than this working tree. After any change under
# benchmark/, bump the version in IMAGE and in container_config.yaml and rerun
# this.
set -eo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-mlcommons/medperf-safety-benchmark:0.0.0}"

docker build -t "$IMAGE" \
    --build-arg "TORCH_INDEX_URL=${TORCH_INDEX_URL:-}" \
    "$HERE"

docker push "$IMAGE"
echo "Pushed $IMAGE"

#!/bin/bash
# Builds the dataset preparation image and publishes it.
#
# Unlike the benchmark script, this one runs on the data owner's own machine,
# before anything is encrypted. It is not part of the trusted computing base.
#
# MedPerf pulls whatever image a container config names, so a run executes the
# published tag rather than this working tree. After any change here, bump the
# version in IMAGE and in container_config.yaml and rerun this.
set -eo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-mlcommons/medperf-safety-benchmark-prep:0.0.0}"

docker build -t "$IMAGE" "$HERE"

docker push "$IMAGE"
echo "Pushed $IMAGE"

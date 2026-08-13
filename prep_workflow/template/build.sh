#!/usr/bin/env bash
# Build the data-preparator image. Run from the orchestrator root so the build
# context includes both the orchestrator package and the author's project.
set -euo pipefail

IMAGE="${1:-my-org/my-data-prep:0.0.1}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CONTEXT="$(dirname "$HERE")"  # examples/prep_workflow

docker build -f "$HERE/Dockerfile" -t "$IMAGE" "$CONTEXT"
echo "Built $IMAGE"

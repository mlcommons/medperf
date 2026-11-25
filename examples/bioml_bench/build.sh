#!/bin/bash
# Builds the example's images and pushes them to a registry. MedPerf pulls
# every image from a registry, and checks it against the hash it was
# registered with, so they must be pushed before being registered.
#
# Usage: bash build.sh [prep] [metrics] [dummy] [aide]    (default: all four)
#
#   REGISTRY   where to push, default docker.io/mhmdk0. The container configs
#              use mhmdk0/...: change their `image:` too if you change this
#   TAG        default 0.0.1
#   PLATFORM   default linux/arm64, for JUPITER's GH200 nodes. Use linux/amd64
#              for x86 machines. Each tag holds one platform, as a plain image
#              manifest: MedPerf's Singularity runner reads the image hash from
#              Docker Hub as a plain manifest, so a multi-platform tag would
#              not match the hash registered from Docker
#
# The images build without emulating the target platform, and the AIDE image
# without downloading its vLLM base image (about 12 GB): see the Dockerfiles.
# Building needs a BuildKit builder that can push directly, which this script
# creates (`docker buildx create --name bioml-bench`) if it doesn't exist.
set -euo pipefail

EXAMPLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY=${REGISTRY:-docker.io/mhmdk0}
TAG=${TAG:-0.0.1}
PLATFORM=${PLATFORM:-linux/arm64}
BUILDER=bioml-bench

declare -A DOCKERFILES=(
  [prep]=data_preparator/Dockerfile
  [metrics]=metrics/Dockerfile
  [dummy]=model_dummy/Dockerfile
  [aide]=model_aide/Dockerfile
)
IMAGES=("$@")
if [ ${#IMAGES[@]} -eq 0 ]; then
  IMAGES=(prep metrics dummy aide)
fi

if ! docker buildx inspect "$BUILDER" > /dev/null 2>&1; then
  docker buildx create --name "$BUILDER" --driver docker-container
fi

for name in "${IMAGES[@]}"; do
  dockerfile=${DOCKERFILES[$name]:?"Unknown image $name: use prep, metrics, dummy or aide"}
  image=$REGISTRY/bioml-bench-$name:$TAG
  echo "=== $image ($PLATFORM)"
  docker buildx build --builder "$BUILDER" --platform "$PLATFORM" \
    --provenance=false --sbom=false \
    --output "type=registry,name=$image,oci-mediatypes=false" \
    -f "$EXAMPLE_DIR/$dockerfile" "$EXAMPLE_DIR"
done

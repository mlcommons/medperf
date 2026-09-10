#!/bin/bash
# Builds the confidential benchmark base image and publishes it.
#
# Not a bare `docker build`: the image carries its own copy of the integrity
# statement contract -- how a statement is encoded and how its hashes are taken
# -- at src/statement.py, and that copy has to stay byte-identical to
# cc/medperf_cc/statement.py, the file whoever verifies a proof runs. A
# disagreement over one byte makes every proof fail to verify with nothing to
# say why, so this refuses to build once the two have drifted.
set -eo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="mlcommons/medperf-confidential-benchmark-base:0.0.1"
CONTRACT="$HERE/../../../cc/medperf_cc/statement.py"
IMAGE_COPY="$HERE/src/statement.py"

for path in "$CONTRACT" "$IMAGE_COPY"; do
    if [[ ! -f "$path" ]]; then
        echo "Cannot find the integrity statement contract at $path" >&2
        exit 1
    fi
done

contract_hash="$(sha256sum "$CONTRACT" | cut -d' ' -f1)"
image_copy_hash="$(sha256sum "$IMAGE_COPY" | cut -d' ' -f1)"

if [[ "$contract_hash" != "$image_copy_hash" ]]; then
    echo "The integrity statement contract and the image's copy have drifted:" >&2
    echo "  $contract_hash  $CONTRACT" >&2
    echo "  $image_copy_hash  $IMAGE_COPY" >&2
    echo "The first is the source of truth. Copy it over the second:" >&2
    echo "  cp $CONTRACT $IMAGE_COPY" >&2
    exit 1
fi

docker build -t "$IMAGE" "$HERE"

docker push "$IMAGE"
echo "Pushed $IMAGE"

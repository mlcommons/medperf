#! /bin/bash
while getopts i:o: flag; do
    case "${flag}" in
    i) IMAGE=${OPTARG} ;;
    o) OUTPUT_PATH=${OPTARG} ;;
    esac
done

if [[ -z "$IMAGE" || -z "$OUTPUT_PATH" ]]; then
    echo "Usage: $0 -i <image> -o <output_path>" >&2
    exit 1
fi

skopeo inspect --format "{{.Digest}}" docker://$IMAGE >$OUTPUT_PATH

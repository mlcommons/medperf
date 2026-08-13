DIR=$(dirname "$(realpath "$0")")
rm -rf "$DIR/workspace/data"
rm -rf "$DIR/workspace/labels"
rm -f "$DIR/workspace/report.yaml"
rm -f "$DIR/workspace/statistics.yaml"

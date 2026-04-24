#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash $SCRIPT_DIR/setup_benchmark_tutorial.sh
# medperf auth logout
cd $SCRIPT_DIR/..
bash $SCRIPT_DIR/setup_model_tutorial.sh
# medperf auth logout
cd $SCRIPT_DIR/..
bash $SCRIPT_DIR/setup_data_tutorial.sh
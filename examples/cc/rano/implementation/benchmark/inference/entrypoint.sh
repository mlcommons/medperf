export LD_LIBRARY_PATH=/usr/local/nvidia/lib64:$LD_LIBRARY_PATH
python /project/benchmark/inference/infer.py $@

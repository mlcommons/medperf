PYTHONSCRIPT="import torch; torch.tensor([1.0, 2.0, 3.0, 4.0]).to('cuda')"
echo "Testing which cuda version to use"
python -c "$PYTHONSCRIPT"
if [ "$?" -ne "0" ]; then
    echo "cuda 12 failed. Trying with cuda 11.8"
    /cuda118/bin/python -c "$PYTHONSCRIPT"
    if [ "$?" -ne "0" ]; then
        echo "No suppored cuda version satisfies the machine driver. Running on CPU."
        python /project/benchmark/inference/infer.py $@
    else
        echo "cuda 11.8 seems to be working. Will use cuda 11.8"
        export NNUNET_EXECUTABLE="/cuda118/bin/nnUNet_predict"
        /cuda118/bin/python /project/benchmark/inference/infer.py $@
    fi
else
    echo "cuda 12 seems to be working. Will use cuda 12"
    python /project/benchmark/inference/infer.py $@
fi

PYTHONSCRIPT="import torch; torch.tensor([1.0, 2.0, 3.0, 4.0]).to('cuda')"

if [ "$1" = "start_aggregator" ] || [ "$1" = "generate_plan" ]; then
    # no need for gpu, don't test cuda
    python /mlcube_project/mlcube.py $@
else
    echo "Testing which cuda version to use"
    python -c "$PYTHONSCRIPT"
    if [ "$?" -ne "0" ]; then
        echo "cuda 12 failed. Trying with cuda 11.8"
        /cuda118/bin/python -c "$PYTHONSCRIPT"
        if [ "$?" -ne "0" ]; then
            echo "No suppored cuda version satisfies the machine driver. Exiting."
            exit 1
        else
            echo "cuda 11.8 seems to be working. Will use cuda 11.8"
            export OPENFL_EXECUTABLE="/cuda118/bin/fx"
            /cuda118/bin/python /mlcube_project/mlcube.py $@
        fi
    else
        echo "cuda 12 seems to be working. Will use cuda 12"
        python /mlcube_project/mlcube.py $@
    fi
fi

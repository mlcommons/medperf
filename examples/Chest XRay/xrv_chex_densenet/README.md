# MLCube: TorchXRayVision models cube
This cube contains an implementation for generating predictions with any of the models implemented inside the `torchxrayvision` library.

## Project Setup
```
# Create Python environment 
virtualenv -p python3 ./env && source ./env/bin/activate

# Install prerequired packages
pip install wheel

# Install MLCube and MLCube docker runner from GitHub repository (normally, users will just run `pip install mlcube mlcube_docker`)
git clone https://github.com/sergey-serebryakov/mlbox.git && cd mlbox && git checkout feature/configV2
cd ./mlcube && python setup.py bdist_wheel  && pip install --force-reinstall ./dist/mlcube-* && cd ..
cd ./runners/mlcube_docker && python setup.py bdist_wheel  && pip install --force-reinstall --no-deps ./dist/mlcube_docker-* && cd ../../..
rm -fr mlbox
```

## Get the cube
```
git clone https://github.com/mlcommons/medical.git && cd ./medical
git fetch origin pull/3/head:cubes && git checkout cubes
cd ./cubes/xrv_models/mlcube
```

## Get the data
The dataset should be retrieved and prepared following the TorchXRayVision Data Preparation Cube instructions. Then, copy the `data` folder from that cube's workspace into this one. Alternatively, you can run all of this cube's tasks pointing to the data preparation cube's workspace by adding the `--workspace=<path_to_workspace>` CLI argument.

## Cube configuraiton
You can define what model to use inside the `parameters.yaml` file. The name of each model follows the library's naming convention.

## Run cube on a local machine with Docker runner
```
mlcube run --task infer # Generate predictions on the prepared dataset
```

Parameters defined in `mlcube.yaml` can be overridden using: `param=input`, example:

```
mlcube run --task infer data_dir=path_to_custom_dir
```

We are targeting pull-type installation, so MLCubes should be available on docker hub. If not, try this:

```
mlcube run ... -Pdocker.build_strategy=auto
```
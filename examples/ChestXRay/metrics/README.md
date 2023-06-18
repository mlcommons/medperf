# MLCube: Metrics cube
This cube contains all the logic required for evaluating the output of a model. It does this given a csv file containing the predictions for a dataset and the labels of such dataset.

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
cd ./cubes/metrics/mlcube
```

## Cube configuraiton
You can adjust the `parameters.yaml` file to your needs. This file specifies the following key-value pairs used for model evaluation:
- `metrics`: a list of metrics to be used for evaluation
- `label columns`: a list of columns that are shared by both the ground-truth and predictions files. This are the columns that the metrics will be executed on.
- `id column`: shared column that identifies a data entry. Used for matching a prediction with the corresponding ground-truth labels

## Run cube on a local machine with Docker runner
This cube expects at least two extra files inside the workspace for model evaluation: 
- `predictions.csv`: A csv file containing the model-generated predictions
- `labels.csv`: A csv file containing the ground-truth labels

```
mlcube run --task evaluate # Executes model evaluation
```

Parameters defined in `mlcube.yaml` can be overridden using: `param=input`, example:

```
mlcube run --task evaluate data_dir=path_to_custom_dir
```

We are targeting pull-type installation, so MLCubes should be available on docker hub. If not, try this:

```
mlcube run ... -Pdocker.build_strategy=auto
```
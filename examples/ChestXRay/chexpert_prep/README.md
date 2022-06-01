# CheXpert Data Preparation Cube
Example of a data preparation cube written for the CheXpert Dataset format. This is a toy example that showcases how we can use MLCube to perform preprocessing tasks on a dataset. 

## Purpose of a Data Preparation Cube
Ideally, data preparation cubes are written for a specific benchmark in mind, and are intended to accept multiple common data formats and transforms them into a single standard format. Data preparation cubes are expected to create a new version of the data, leaving the original input data untouched.

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
This folder contains all the required files to build the cube. Therefore, to get the cube, run this:
```
git clone https://github.com/mlcommons/medical.git && cd ./medical
git fetch origin pull/3/head:cubes && git checkout cubes
cd ./cubes/chexpert_prep/mlcube
```

## Get the data
Because the Chexpert Dataset contains sensitive information, signing an user agreement is required before obtaining the data. This means that we cannot automate the data download process. To obtain the dataset:

sign up at the Chexpert Dataset Download Agreement and download the small dataset from the link sent to your email.
Unzip and place the CheXpert-v1.0-small folder inside `mlcube/workspace` folder. Your folder structure should look like this:
```
.
├── mlcube
│   └── workspace
│       ├── CheXpert-v1.0-small
│       │   ├── valid
│       │  	└── valid.csv
│       └── parameters.yaml
└── project
```
# Run cube on a local machine with Docker runner
```
mlcube run --task preprocess # Creates new version of the data into /data
mlcube run --task sanity_check # checks that the output format is okay
mlcube run --task statistics # Calculates data statistics into statistics.yaml
```
Parameters defined in mlcube.yaml can be overridden using: param=input, example:
```
mlcube run --task preprocess data_path=path_to_custom_dir
```
We are targeting pull-type installation, so MLCubes should be available on docker hub. If not, try this:

```
mlcube run ... -Pdocker.build_strategy=auto
```
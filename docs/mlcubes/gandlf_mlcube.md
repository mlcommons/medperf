<!-- ---
demo_url: https://storage.googleapis.com/medperf-storage/mock_xrv_demo_data.tar.gz
model_add: https://storage.googleapis.com/medperf-storage/xrv_chex_densenet.tar.gz
assets_url: https://raw.githubusercontent.com/hasan7n/medperf/88155cf4cac9b3201269d16e680d7d915a2f8adc/examples/ChestXRay/
tutorial_id: benchmark
--- -->

# Creating a GaNDLF MLCube

<!-- {% set prep_mlcube = assets_url+"chexpert_prep/mlcube/mlcube.yaml" %} -->

## Overview

This guide will walk you through how to wrap a model trained using GaNDLF(link) as a MedPerf-compatible MLCube ready to be used for **inference** (i.e. as a Model MLCube(link)). The steps can be summarized as follows:

1. Train a GaNDLF Model
2. Deploy the Model

We assume that you have medperf installed?(link).

## Before We Start

#### Install GaNDLF

Make sure you have GaNDLF installed (link).

#### Download the Necessary files

We provide a script that downloads necessary files so that you follow the tutorial smoothly. Run the following: (make sure you are in MedPerf's root folder)

```bash
sh tutorials_scripts/setup_GaNDLF_mlcube_tutorial.sh
```

This will create a workspace folder `medperf_tutorial` where all necessary files are downloaded.

## 1. Train a GaNDLF Model

We will first train a small model using GaNDLF. You can skip this step if you already have a trained model.

Under the workspace folder `medperf_tutorial`, you will find:

```bash
gandlf_run \
  -c ./config_classification.yaml \
  -i ./inputs.csv \
  -m ./trained_model_output \
  -t True \
  -d cuda
```

You will have your trained model and all related files in the folder `trained_model_output`.

## 2. Create an MLCube File

We provide a cookiecutter to create an MLCube file that is ready to be consumed by `gandlf_deploy` and produce a MLCube ready to be used by MedPerf.

```bash
medperf mlcube create gandlf
```

you will be prompted...

## 3. Deploy the GaNDLF Model as an MLCube

```bash
gandlf_deploy \
  -c ./config_classification.yaml \
  -m ./trained_model_output \
  --target docker \
  --mlcube-root ./my_mlcube_dir \
  -o ./output_dir
```

That's it! also run docker image ls you will see stuff

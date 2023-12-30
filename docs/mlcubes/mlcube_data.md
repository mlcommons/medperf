---
name: Data Preparator MLCube
url: https://github.com/mlcommons/medperf/tree/main/examples/chestxray_tutorial/data_preparator
data_url: https://storage.googleapis.com/medperf-storage/chestxray_tutorial/sample_prepared_data.tar.gz
---
# {{ page.meta.name }}

## Introduction

This is one of the three guides that help the user build MedPerf-compatible MLCubes. The other two guides are for building a [Model MLCube](mlcube_models.md) and a [Metrics MLCube](mlcube_metrics.md). Together, the three MLCubes examples constitute a complete benchmark workflow for the task of thoracic disease detection from Chest X-rays. 

To recap, a final working MedPerf pipeline consists of the following steps:

1. Data Owner exports a raw dataset from one's databases (manually or with scripts) - this step is made outside the pipeline itself. The result is some `my_raw_data/` folder. If pipeline is run by some other person (Model Owner / Benchmark Owner), predefined `my_benchmark_demo_raw_data/` is used (created by Benchmark Owner and distributed with the specific benchmark).
2. Data Preparator MLCube takes this folder path as input and transforms it to some unified format, outputting some `my_prepared_dataset/` folder (MLCube is implemented by Benchmark Owner)
3. Model MLCube takes this prepared data and infers some model over it, saving results into some `my_model_predictions/` folder. (MLCube is implemented by Model Owner; Benchmark Owner has to implement a sample baseline model cube to be used as mock-up)
4. Metrics MLCube processes predictions and evaluate some metrics, outputting them to some `my_metrics.json` file (MLCube is implemented by Benchmark Owner)
5. Data Owner receives metrics results and can submit them to MedPerf server.

These three guides describe 2-4 steps. As all steps are demonstrating how to build a specific MLCube, it's highly recommended to explore a [Model MLCube guide](mlcube_models.md) firstly that explains not only Model part, but the sense and detailed structure of MLCubes itself. Another option is to explore [MLCube basic docs](https://mlcommons.github.io/mlcube/). In this guide the shortened version is described.

## About this Guide

This guide will help users familiarize themselves with the expected interface of the Data Preparator MLCube and gain a comprehensive understanding of its components. By following this walkthrough, users will gain insights into the structure and organization of a Model MLCube, allowing them at the end to be able to implement their own MedPerf-compatible Model MLCube.

The guide will start by providing general advice, steps, and required API on building these MLCubes. Then, you will be guided to create your own MLCube from template - using the Chest X-ray Data Preprocessor MLCube as a working example.

It is considered a good practice to be able to handle data in different formats: say, if the benchmark processes images, it's worth to support JPEGs, PNGS, BMPs and well as other expected images formats; support big images as well as small ones; etc. Therefor you simplify the work for your users (Dataset Owners) as they can export the data in a most handy format for them. It's Data Preparator responsibility to  convert all reasonable input data to some unified format. 

## Before Building the MLCube

You would have to implement three tasks that your MLCube should handle:
- `prepare`: your main task that converts raw input data into unified format
- `sanity_check`: checks that `prepare` outputs are clean and consistent (say, there is no records without ground truth labels, labels do have only expected values only, the data fields have reasonable values without outliers and NaNs, etc.)
- `statistics`: Allows you to calculate some aggregated statistics over the transformed dataset. That statistics would be uploaded to you as Benchmark Owner once Dataset Owner submits their dataset.

It is assumed that you do already have 

- Some raw data
- Expected unified format that data should be converted to
- A working implementation of all these three parts.

What you want to accomplish through this guide is to wrap your preparation code within an MLCube. Make sure you extract each part of your logic, so it can be run independently of each other.

## Required API

During execution of every command, the specific params are passed. Despite your code can be implemented in any way that you want, keep in mind that you should support the folowing API:

### Data preparation API (`prepare` command)

The following values are passed while 
- `data_path`: path to r/o folder that contains raw data
- `labels_path`: path to r/o folder that contains raw ground truth labels
- any other optional extra params that you attach to the MLCube. Say, a `.txt` file with a list of acceptable labels. NB: while first two params contain user data, these extra params would contain values defined by you as MLCube owner. So, no, you cannot require your users to pass additional data.
- `output_path`: r/w folder to store transformed dataset objects
- `output_labels_path`: r/w folder to store transformed labels

### Sanity check API (`sanity_check` command)

- `data_path`: path to r/o folder that contains **transformed** data
- `labels_path`: path to r/o folder that contains **transformed** ground truth labels
- any other optional extra params that you attach to the MLCube - same as for `prepare` command.

Sanity check is not expected to return any outputs: it either runs successfully, or fails.

### Statistics API (`statistics` command)

- `data_path`: path to r/o folder that contains **transformed** data
- `labels_path`: path to r/o folder that contains **transformed** ground truth labels
- any other optional extra params that you attach to the MLCube - same as for `prepare` command.
- `output_path`: path to `.yaml` file where your code should write down calculated statistics.

## Build your own MLCube

While that guide leads you through creating your own MLCube, you can always check a prebuilt example to understand better how it works in a already implemented MLCube. The example is stored [here](https://github.com/mlcommons/medperf/tree/main/examples/chestxray_tutorial/data_preparator):
```bash
cd examples/chestxray_tutorial/data_preparator/
```

The guide shows this implementation to describe concepts.

### Use an MLCube Template

First, make sure you have [MedPerf installed](../getting_started/installation.md). You can create a Data Preparator MLCube template by running the following command:

```bash
medperf mlcube create data_preparator
```

You will be prompted to fill in some configuration options through the CLI. Below are the options and their default values:

```bash
project_name [Data Preparator MLCube]: # (1)!
project_slug [data_preparator_mlcube]: # (2)!
description [Data Preparator MLCube Template. Provided by MLCommons]: # (3)!
author_name [John Smith]: # (4)!
accelerator_count [0]: # (5)!
docker_image_name [docker/image:latest]: # (6)!
```

1. Gives a Human-readable name to the MLCube Project.
2. Determines how the MLCube root folder will be named.
3. Gives a Human-readable description to the MLCube Project.
4. Documents the MLCube implementation by specifying the author.
5. Indicates how many GPUs should be visible by the MLCube.
6. MLCubes use Docker containers under the hood. Here, you can provide an image tag to the image that will be created by this MLCube. **You should use a valid name that allows you to upload it to a Docker registry.**

After filling the configuration options, the following directory structure will be generated:

```bash
.
└── data_preparator_mlcube
    ├── mlcube
    │   ├── mlcube.yaml
    │   └── workspace
    │       └── parameters.yaml
    └── project
        ├── Dockerfile
        ├── mlcube.py
        └── requirements.txt
```

### The `project` folder

This is where your inference logic will live. It contains a standard Docker image project with a specific entrypoint's API. `mlcube.py` contains an entrypoint and handles all the tasks we've described. You need to update this template with your code and bind your logic to specified functions for all three commands.
You may check the [Chest X-ray tutorial example](https://github.com/mlcommons/medperf/blob/main/examples/chestxray_tutorial/data_preparator/project/mlcube.py) to see how it should look like:

```python title="mlcube.py"
--8<-- "examples/chestxray_tutorial/data_preparator/project/mlcube.py"
```

### The `mlcube` folder

This folder is mainly for configuring your MLCube and providing additional files the MLCube may interact with, such as parameters or model weights.

#### `mlcube.yaml` MLCube configuration


The `mlcube.yaml` file contains metadata and configuration of your mlcube. This file was already populated with the configuration you provided during the step of creating the template. There is no need to edit anything in this file except if you are specifying extra parameters to the commands (e.g., sklearn's `StardardScaler` weights or any other parameters required for data transformation).

```python title="mlcube.py"
--8<-- "examples/chestxray_tutorial/data_preparator/mlcube/mlcube.yaml"
```

All paths are relative to `mlcube/workspace/` folder.

To set up additional inputs you should add a key-value pair in the task's `inputs` dictionary: 

```yaml title="mlcube.yaml" hl_lines="9"
...
  prepare:
    parameters:
      inputs:
        {
          data_path: input_data,
          labels_path: input_labels,
          parameters_file: parameters.yaml,
          standardscaler_weights: additional_files/standardscaler.pkl
        }
      outputs: { output_path: data/, output_labels_path: labels/ }
...
```

Taking into account a note about paths location, this new file should be stored at `mlcube/workspace/additional_files/standardscaler.pkl`

#### Parameters

Your preprocessing logic may depend on some parameters (e.g. which labels are accepted). It is usually a more favorable design to not hardcode such parameters, but instead pass them when running the MLCube. This can be done by having a `parameters.yaml` file as an input to the MLCube. This file will be available to the commands described before (if you declare it in `inputs` dict of specific command). You can parse this file in the `mlcube.py` file and pass its contents to your code.

This file should be placed in the `mlcube/workspace` folder.

## Build your MLCube

After you follow the previous sections and fulfill the image with your logics, the MLCube is ready to be built and run. Run the command below to build the MLCube. Make sure you are in the `mlcube/` subfolder of your Data Preparator.

```bash
mlcube configure -Pdocker.build_strategy=always
```

This command will build your docker image and make the MLCube ready to use.

## Run your MLCube

MedPerf will take care of running your MLCube. However, it's recommended to test the MLCube alone before using it with MedPerf for better debugging.

Use the command below to run the MLCube. Make sure you are in the `mlcube/` subfolder of your Data Preparator.

```bash
mlcube run --task prepare data_path=<path_to_raw_data> labels_path=<path_to_raw_labels> output_path=<path_to_save_transformed_data> output_labels_path=<path_to_save_transformed_labels>
```

!!! note "Relative paths"
    Keep in mind that though we are running tasks from `mlcube/`, all the paths should be absolute or relative to `mlcube/workspace/`

!!! note "Default values"
    We have declared a default values for every path parameter. It means that we can skip this params in our command.

    Say you have the following structure: 
    ```bash
    .
    └── data_preparator_mlcube
        ├── mlcube
        │   ├── mlcube.yaml
        │   └── workspace
        │       └── parameters.yaml
        └── project
            └── ...
    └── my_data
        ├── data
        │   ├── ...
        └── labels
            └── ...
    ```
    
    Now you can run the following commands, being located at `data_preparator_mlcube/mlcube`:
    ```
    mlcube run --task prepare data_path=../../my_data/data/ labels_path=../../my_data/labels/
    mlcube run --task sanity_check
    mlcube run --task statistics output_path=../../my_data/statistics.yaml
    ```
    
    Note how

    1. Passed paths are relative to `mlcube/workspace` rather then to current working directory,
    2. We used default values for transformed data so new folders would appear: `mlcube/workspace/data/` and others. 

## Using the Example with GPUs

The provided example codebase runs only on CPU. You can modify it to have `pytorch` run inference on a GPU.

The general instructions for building an MLCube to work with a GPU are the same as the provided instructions, but with the following slight modifications:

- Use a number different than `0` for the `accelerator_count` that you will be prompted with when creating the MLCube template.
- Inside the `docker` section of the `mlcube.yaml`, add a key value pair: `gpu_args: --gpus=all`. These `gpu_args` will be passed to `docker run` under the hood by MLCube. You may add more than just `--gpus=all`.
- Make sure you install the required GPU dependencies in the docker image. For instance, this may be done by simply modifying the `pip` dependencies in the `requirements.txt` file to download `pytorch` with cuda, or by changing the base image of the dockerfile.

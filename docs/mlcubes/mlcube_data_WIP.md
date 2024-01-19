---
name: Data Preparator MLCube
url: https://github.com/mlcommons/medperf/tree/main/examples/chestxray_tutorial/data_preparator
---
TODO: Change the structure to align with mlcube_models, to help users wrap their existing code into mlcube

# {{ page.meta.name }}

## Introduction

This guide is one of three designed to assist users in building MedPerf-compatible MLCubes. The other two guides focus on creating a [Model MLCube](mlcube_models.md) and a [Metrics MLCube](mlcube_metrics.md). Together, these three MLCubes form a complete benchmark workflow for the task of thoracic disease detection from Chest X-rays.

In summary, a functional MedPerf pipeline includes these steps:

1. The Data Owner exports a raw dataset from their databases (manually or via scripts) - this step occurs outside the pipeline itself. Let's name the output folder as `my_raw_data/`. If the pipeline is run by another person (Model Owner/Benchmark Owner), a predefined `my_benchmark_demo_raw_data/` would be used instead (created and distributed by the Benchmark Owner).
2. The Data Preparator MLCube takes this folder's path as input and converts data into a standardized format, resulting in some `my_prepared_dataset/` folder (MLCube is implemented by the Benchmark Owner).
3. The Model MLCube processes the prepared data, running a model and saving the results in some `my_model_predictions/` folder (MLCube is implemented by the Model Owner; the Benchmark Owner must implement a baseline model MLCube to be used as a mock-up).
4. The Metrics MLCube processes predictions and evaluates metrics, saving them in some `my_metrics.yaml` file (MLCube implemented by the Benchmark Owner).
5. The Data Owner reviews the metric results and may submit them to the MedPerf server.

Aforementioned guides detail steps 2-4. As all steps demonstrate building specific MLCubes, we recommend starting with the [Model MLCube guide](mlcube_models.md), which offers a more detailed explanation of the MLCube's concept and structure. Another option is to explore [MLCube basic docs](https://mlcommons.github.io/mlcube/). In this guide provides the shortened concepts description, focusing on nuances and input/output parameters.

## About this Guide

This guide describes the tasks, structure and input/output parameters of Data Preparator MLCube, allowing users at the end to be able to implement their own MedPerf-compatible MLCube for Benchmark purposes.

The guide starts with general advices, steps, and the required API for building these MLCubes. Subsequently, it will lead you through creating your MLCube using the Chest X-ray Data Preprocessor MLCube as a practical example.

It's considered best practice to handle data in various formats. For instance, if the benchmark involves image processing, it's beneficial to support JPEGs, PNGs, BMPs, and other expected image formats; accommodate large and small images, etc. Such flexibility simplifies the process for Dataset Owners, allowing them to export data in their preferred format. The Data Preparator's role is to convert all reasonable input data into a unified format.

## Before Building the MLCube

Your MLCube must implement three command tasks:

- `prepare`: your main task that transforms raw input data into a unified format.
- `sanity_check`: verifies the cleanliness and consistency of `prepare` outputs (e.g., ensuring no records lack ground truth labels, labels contain only expected values, data fields are reasonable without outliers or NaNs, etc.)
- `statistics`: Calculates some aggregated statistics on the transformed dataset. Once the Dataset Owner submits their dataset, these statistics will be uploaded to you as the Benchmark Owner.

It's assumed that you already have:

- Some raw data.
- The expected unified format for data conversion.
- A working implementation of all three tasks.

This guide will help you encapsulate your preparation code within an MLCube. Make sure you extracted each part of your logic, so it can be run independently.


## Required API

Each command execution receives specific parameters. While you are flexible in code implementation, keep in mind that your implementation will receive the following input arguments:

### Data Preparation API (`prepare` Command)

The parameters include:
- `data_path`: the path to the raw data folder (read-only).
- `labels_path`: the path to the ground truth labels folder (read-only).
- Any other optional extra params that you attach to the MLCube, such as path to `.txt` file with acceptable labels. Note: these extra parameters contain values defined by you, the MLCube owner, not the users' data.
- `output_path`: an r/w folder for storing transformed dataset objects.
- `output_labels_path`: an r/w folder for storing transformed labels.

### Sanity Check API (`sanity_check` Command)

The parameters include:
- `data_path`: the path to the transformed data folder (read-only).
- `labels_path`: the path to the transformed ground truth labels folder (read-only).
- Any other optional extra params that you attach to the MLCube - same as for the `prepare` command.

The sanity check does not produce outputs; it either completes successfully or fails.

### Statistics API (`statistics` Command)

- `data_path`: the path to the transformed data folder (read-only).
- `labels_path`: the path to the transformed ground truth labels folder (read-only).
- Any other optional extra params that you attach to the MLCube - same as for `prepare` command.
- `output_path`: path to `.yaml` file where your code should write down calculated statistics.

## Build Your Own MLCube

While this guide leads you through creating your own MLCube, you can always check a prebuilt example for a better understanding of how it works in an already implemented MLCube. The example is available [here](https://github.com/mlcommons/medperf/tree/main/examples/chestxray_tutorial/data_preparator):
```bash
cd examples/chestxray_tutorial/data_preparator/
```

The guide uses this implementation to describe concepts.

### Use an MLCube Template

First, ensure you have [MedPerf installed](../getting_started/installation.md). Create a Data Preparator MLCube template by running the following command:

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
5. Specifies how many GPUs should be visible by the MLCube.
6. MLCubes use Docker containers under the hood. Here, you can provide an image tag for the image created by this MLCube. **You should use a valid name that allows you to upload it to a Docker registry.**

After filling the configuration options, the following directory structure will be generated:

```bash
.
└── evaluator_mlcube
    ├── mlcube
    │   ├── mlcube.yaml
    │   └── workspace
    │       └── parameters.yaml
    └── project
        ├── Dockerfile
        ├── mlcube.py
        └── requirements.txt
```

### The `project` Folder

This is where your preprocessing logic will live. It contains a standard Docker image project with a specific API for the entrypoint. `mlcube.py` contains the entrypoint and handles all the tasks we've described. Update this template with your code and bind your logic to specified functions for all three commands.
Refer to the [Chest X-ray tutorial example](https://github.com/mlcommons/medperf/blob/main/examples/chestxray_tutorial/data_preparator/project/mlcube.py) for an example of how it should look:

```python title="mlcube.py"
--8<-- "examples/chestxray_tutorial/data_preparator/project/mlcube.py"
```

### The `mlcube` Folder

This folder is primarily for configuring your MLCube and providing additional files the MLCube may interact with, such as parameters or model weights.

#### `mlcube.yaml` MLCube Configuration

The `mlcube/mlcube.yaml` file contains metadata and configuration of your mlcube. This file is already populated with the configuration you provided during the template creation step. There is no need to edit anything in this file except if you are specifying extra parameters to the commands (e.g., you want to pass a sklearn's `StardardScaler` weights or any other parameters required for data transformation).

```python title="mlcube.py"
--8<-- "examples/chestxray_tutorial/data_preparator/mlcube/mlcube.yaml"
```

All paths are relative to `mlcube/workspace/` folder.

To set up additional inputs, add a key-value pair in the task's `inputs` dictionary: 

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

Considering the note about path locations, this new file should be stored at `mlcube/workspace/additional_files/standardscaler.pkl`

#### Parameters

Your preprocessing logic might depend on certain parameters (e.g., which labels are accepted). It is generally better to pass such parameters when running the MLCube, rather than hardcoding them. This can be done via a `parameters.yaml` file  that is passed to the MLCube. This file will be available to the previously described commands (if you declare it in the `inputs` dict of a specific command). You can parse this file in the `mlcube.py` file and pass its contents to your logic.

This file should be placed in the `mlcube/workspace` folder.

## Build Your MLCube

After you follow the previous sections and fulfill the image with your logic, the MLCube is ready to be built and run. Run the command below to build the MLCube. Ensure you are in the `mlcube/` subfolder of your Data Preparator.

```bash
mlcube configure -Pdocker.build_strategy=always
```

This command builds your Docker image and prepares the MLCube for use.

## Run Your MLCube

MedPerf will take care of running your MLCube. However, it's recommended to test the MLCube alone before using it with MedPerf for better debugging.

To run the MLCube, use the command below. Ensure you are located in the `mlcube/` subfolder of your Data Preparator.

```bash
mlcube run --task prepare data_path=<path_to_raw_data> \
  labels_path=<path_to_raw_labels> \
  output_path=<path_to_save_transformed_data> \
  output_labels_path=<path_to_save_transformed_labels>
```

!!! note "Relative paths"
    Keep in mind that though we are running tasks from `mlcube/`, all the paths should be absolute or relative to `mlcube/workspace/`.

!!! note "Default values"
    We have declared a default values for every path parameter. This allows for omitting these parameters in our commands.

    Consider the following structure: 
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
    
    Now, you can execute the commands below, being located at `data_preparator_mlcube/mlcube/`:
    ```
    mlcube run --task prepare data_path=../../my_data/data/ labels_path=../../my_data/labels/
    mlcube run --task sanity_check
    mlcube run --task statistics output_path=../../my_data/statistics.yaml
    ```
    
    Note that:

    1. The passed paths are relative to `mlcube/workspace` rather then to the current working directory,
    2. We used default values for transformed data so new folders would appear: `mlcube/workspace/data/` and others. 

## Using the Example with GPUs

The provided example codebase runs only on CPU. You can modify it to pass a GPU inside Docker image if your code utilizes it.

The general instructions for building an MLCube to work with a GPU are the same as the provided instructions, but with the following slight modifications:

- Enter a number different than `0` for the `accelerator_count` that you will be prompted with when creating the MLCube template or modify `platform.accelerator_count` value of `mlcube.yaml` configuration.
- Inside the `docker` section of the `mlcube.yaml`, add a key value pair: `gpu_args: --gpus=all`. These `gpu_args` will be passed to `docker run` command by MLCube. You may add more than just `--gpus=all`.
- Make sure you install the required GPU dependencies in the docker image. For instance, this may be done by simply modifying the `pip` dependencies in the `requirements.txt` file to download `pytorch` with cuda, or by changing the base image of the dockerfile.

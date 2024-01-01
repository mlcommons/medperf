---
name: Metrics/Evaluator MLCube
url: https://github.com/mlcommons/medperf/tree/main/examples/chestxray_tutorial/metrics
data_url: https://storage.googleapis.com/medperf-storage/chestxray_tutorial/sample_prepared_data.tar.gz
---
# {{ page.meta.name }}

## Introduction

This guide is one of three designed to assist users in building MedPerf-compatible MLCubes. The other two guides focus on creating a [Data Preparator MLCube](mlcube_data.md) and a [Model MLCube](mlcube_models.md). Together, these three MLCubes form a complete benchmark workflow for the task of thoracic disease detection from Chest X-rays.

In summary, a functional MedPerf pipeline includes these steps:

1. The Data Owner exports a raw dataset from their databases (manually or via scripts) - this step occurs outside the pipeline itself. Lets name the output folder as `my_raw_data/`. If the pipeline is run by another person (Model Owner/Benchmark Owner), a predefined `my_benchmark_demo_raw_data/` would be used instead (created and distributed by the Benchmark Owner).
2. The Data Preparator MLCube takes this folder's path as input and converts data into a standardized format, resulting in some `my_prepared_dataset/` folder (MLCube is implemented by the Benchmark Owner).
3. The Model MLCube processes the prepared data, running a model and saving the results in some `my_model_predictions/` folder (MLCube is implemented by the Model Owner; the Benchmark Owner must implement a baseline model MLCube to be used as a mock-up).
4. The Metrics/Evaluator MLCube processes predictions and evaluates metrics, saving them in some `my_metrics.yaml` file (MLCube implemented by the Benchmark Owner).
5. The Data Owner reviews the metric results and may submit them to the MedPerf server.

Aforementioned guides detail steps 2-4. As all steps demonstrate building specific MLCubes, we recommend starting with the [Model MLCube guide](mlcube_models.md), which offers a more detailed explanation of the MLCube's concept and structure. Another option is to explore [MLCube basic docs](https://mlcommons.github.io/mlcube/). In this guide provides the shortened concepts description, focusing on nuances and input/output parameters.

## About this Guide

This guide describes the tasks, structure and input/output parameters of Metrics MLCube, allowing users at the end to be able to implement their own MedPerf-compatible MLCube for Benchmark purposes.

The guide starts with general advices, steps, and the required API for building these MLCubes. Subsequently, it will lead you through creating your MLCube using the Chest X-ray Data Preprocessor MLCube as a practical example.

Note: As the Dataset Owner would share the output of your metrics evaluation with you as Benchmark Owner, ensure that your metrics are not too specific and do not reveal any Personally Identifiable Information (PII) or other confidential data (including dataset statistics) - otherwise, no Dataset Owners would agree to participate in your benchmark.

## Before Building the MLCube

Your MLCube must implement an `evaluate` command that calculates your metrics.

It's assumed that you as Benchmark Owner already have:

- Some raw data.
- Implemented [Data Preparator](mlcube_data.md) and a [Baseline Model](mlcube_models.md) MLCubes as they are foundational to Benchmark pipeline.
- Model predictions are stored at some `my_model_predictions/` folder.
- A working implementation of metric calculations.

This guide will help you encapsulate your preparation code within an MLCube. Make sure you extracted metric calculation logic, so it can be executed independently.


## Required API

During execution, the `evaluation` command will receive specific parameters. While you are flexible in code implementation, keep in mind that your implementation will receive the following input arguments:

- `predictions`: the path to the folder containing your predictions (read-only).
- `labels`: the path to the folder containing [transformed](mlcube_data.md#data-preparation-api-prepare-command) ground truth labels (read-only).
- Any other optional extra params that you attach to the MLCube, such as parameters file. Note: these extra parameters contain values defined by you, the MLCube owner, not the users' data.
- `output_path`: path to `.yaml` file where your code should write down calculated metrics.

## Build Your Own MLCube

While this guide leads you through creating your own MLCube, you can always check a prebuilt example for a better understanding of how it works in an already implemented MLCube. The example is available [here]({{url}}):
```bash
cd examples/chestxray_tutorial/metrics/
```

The guide uses this implementation to describe concepts.

### Use an MLCube Template

First, ensure you have [MedPerf installed](../getting_started/installation.md). Create a Metrics MLCube template by running the following command:

```bash
medperf mlcube create evaluator
```

You will be prompted to fill in some configuration options through the CLI. Below are the options and their default values:

```bash
project_name [Evaluator MLCube]: # (1)!
project_slug [evaluator_mlcube]: # (2)!
description [Evaluator MLCube Template. Provided by MLCommons]: # (3)!
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

### The `project` Folder

This is where your metrics logic will live. It contains a standard Docker image project with a specific API for the entrypoint. `mlcube.py` contains the entrypoint and handles the `evaluate` task. Update this template with your code and bind your logic to specified command entry-point function.
Refer to the [Chest X-ray tutorial example](https://github.com/mlcommons/medperf/blob/main/examples/chestxray_tutorial/metrics/project/mlcube.py) for an example of how it should look:

```python title="mlcube.py"
--8<-- "examples/chestxray_tutorial/metrics/project/mlcube.py"
```

### The `mlcube` Folder

This folder is primarily for configuring your MLCube and providing additional files the MLCube may interact with, such as parameters or model weights.

#### `mlcube.yaml` MLCube Configuration

The `mlcube/mlcube.yaml` file contains metadata and configuration of your mlcube. This file is already populated with the configuration you provided during the template creation step. There is no need to edit anything in this file except if you are specifying extra parameters to the commands.

```python title="mlcube.py"
--8<-- "examples/chestxray_tutorial/metrics/mlcube/mlcube.yaml"
```

All paths are relative to `mlcube/workspace/` folder.

To set up additional inputs, add a key-value pair in the task's `inputs` dictionary: 

```yaml title="mlcube.yaml" hl_lines="9"
...
  prepare:
    parameters:
      inputs:
        {
          predictions: predictions,
          labels: labels,
          parameters_file: parameters.yaml,
          some_additional_file_with_weights: additional_files/my_weights.zip
        }
      outputs: { output_path: { type: "file", default: "results.yaml" } }
...
```

Considering the note about path locations, this new file should be stored at `mlcube/workspace/additional_files/my_weights.zip`.

#### Parameters

Your metrics evaluation logic might depend on certain parameters (e.g., proba threshold for classifying predictions). It is generally better to pass such parameters when running the MLCube, rather than hardcoding them. This can be done via a `parameters.yaml` file that is passed to the MLCube. You can parse this file in the `mlcube.py` file and pass its contents to your logic.

This file should be placed in the `mlcube/workspace` folder.

## Build Your MLCube

After you follow the previous sections and fulfill the image with your logic, the MLCube is ready to be built and run. Run the command below to build the MLCube. Ensure you are in the `mlcube/` subfolder of your Evaluator.

```bash
mlcube configure -Pdocker.build_strategy=always
```

This command builds your Docker image and prepares the MLCube for use.

## Run Your MLCube

MedPerf will take care of running your MLCube. However, it's recommended to test the MLCube alone before using it with MedPerf for better debugging.

To run the MLCube, use the command below. Ensure you are located in the `mlcube/` subfolder of your Data Preparator.

```bash
mlcube run --task evaluate predictions=<path_to_predictions> \
 labels=<path_to_transformed_labels> \
 output_path=<path_to_yaml_file_to_save>
```

!!! note "Relative paths"
    Keep in mind that though we are running tasks from `mlcube/`, all the paths should be absolute or relative to `mlcube/workspace/`.

!!! note "Default values"
    Default values are set for every path parameter, allowing for their omission in commands. For example, in the discussed Chest X-Ray example, the `predictions` input is defined as follows:
    ```python hl_lines="3"
    ...
      inputs:
        {
          predictions: predictions,
          labels: labels,
        }
    ...
    ```

    If this parameter is omitted (e.g., running MLCube with default parameters by `mlcube run --task evaluate`), it's assumed that predictions are stored in the `mlcube/workspace/predictions/` folder.

## Using the Example with GPUs

The provided example codebase runs only on CPU. You can modify it to pass a GPU inside Docker image if your code utilizes it.

The general instructions for building an MLCube to work with a GPU are the same as the provided instructions, but with the following slight modifications:

- Enter a number different than `0` for the `accelerator_count` that you will be prompted with when creating the MLCube template or modify `platform.accelerator_count` value of `mlcube.yaml` configuration.
- Inside the `docker` section of the `mlcube.yaml`, add a key value pair: `gpu_args: --gpus=all`. These `gpu_args` will be passed to `docker run` command by MLCube. You may add more than just `--gpus=all`.
- Make sure you install the required GPU dependencies in the docker image. For instance, this may be done by simply modifying the `pip` dependencies in the `requirements.txt` file to download `pytorch` with cuda, or by changing the base image of the dockerfile.

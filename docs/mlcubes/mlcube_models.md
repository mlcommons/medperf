---
name: Model MLCube
url: https://github.com/mlcommons/medperf/examples/chestxray/model_custom_cnn
data_url: https://storage.googleapis.com/medperf-storage/chestxray_tutorial/sample_prepared_data.tar.gz
weights_url: https://storage.googleapis.com/medperf-storage/chestxray_tutorial/cnn_weights.tar.gz
---
# {{ page.meta.name }}

## Introduction

This is one of the three guides that help the user build MedPerf-compatible MLCubes. The other two guides are for building a [Data Preparator MLCube](mlcube_data.md) and a [Metrics MLCube](mlcube_metrics.md). Together, the three MLCubes examples constitute a complete benchmark workflow for the task of thoracic disease detection from Chest X-rays.

## About this Guide

This guide will help users familiarize themselves with the expected interface of the Model MLCube and gain a comprehensive understanding of its components. By following this walkthrough, users will gain insights into the structure and organization of a Model MLCube, allowing them at the end to be able to implement their own MedPerf-compatible Model MLCube.

The guide will start by providing general advice, steps, and hints on building these MLCubes. Then, an example will be presented through which the provided guidance will be applied step-by-step to build a Chest X-ray classifier MLCube. The final MLCube code can be found [here]({{ page.meta.url }}).

## Before Building the MLCube

It is assumed that you already have a working code that runs inference on data and generates predictions, and what you want to accomplish through this guide is to wrap your inference code within an MLCube.

- Make sure you decouple your inference logic from the other machine learning common pipelines (e.g.; training, metrics, ...).
- Your inference logic can be written in any structure, can be split into any number of files, can represent any number of inference stages, etc..., **as long as the following hold**:
    - The whole inference flow can be invoked by a single command/function.
    - This command/function has **at least** the following arguments:
        - A string representing a path that points to all input data records
        - A string representing a path that points to the desired output directory where the predictions will be stored.
- Your inference logic should not alter the input files and folders.
- Your inference logic should expect the input data in a certain structure. This is usually determined by following the specifications of the benchmark you want to participate in.
- Your inference logic should save the predictions in the output directory in a certain structure. This is usually determined by following the specifications of the benchmark you want to participate in.

## Use an MLCube Template

MedPerf provides MLCube templates. You should start from a template for faster implementation and to build MLCubes that are compatible with MedPerf.

First, make sure you have [MedPerf installed](../getting_started/installation.md). You can create a model MLCube template by running the following command:

```bash
medperf mlcube create model
```

You will be prompted to fill in some configuration options through the CLI. Below are the options and their default values:

```bash
project_name [Model MLCube]: # (1)!
project_slug [model_mlcube]: # (2)!
description [Model MLCube Template. Provided by MLCommons]: # (3)!
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
└── model_mlcube
    ├── mlcube
    │   ├── mlcube.yaml
    │   └── workspace
    │       └── parameters.yaml
    └── project
        ├── Dockerfile
        ├── mlcube.py
        └── requirements.txt
```

The next sections will go through the contents of this directory in details and customize it.

### The `project` folder

This is where your inference logic will live. This folder initially contains three files as shown above. The upcoming sections will cover their use in details.

The first thing to do is put your code files in this folder.

#### How will the MLCube identify your code?

This is done through the `mlcube.py` file. This file defines the interface of the MLCube and should be linked to your inference logic.

```python title="mlcube.py"
--8<-- "docs/snippets/model_mlcube/mlcube.py"
```

As shown above, this file exposes a command `infer`. It's basic arguments are the input data path, the output predictions path, and a parameters file path.

The parameters file, as will be explained in the upcoming sections, gives flexibility to your MLCube. For example, instead of hardcoding the inference batch size in the code, it can be configured by passing a parameters file to your MLCube which contains its value. This way, your same MLCube can be reused with multiple batch sizes by just changing the input parameters file.

You should ignore the `hotfix` command as described in the file.

The `infer` command will be automatically called by the MLCube when it's built and run. This command should call your inference logic. Make sure you replace its contents with a code that calls your inference logic. This could be by importing a function from your code files and calling it with the necessary arguments.

#### Prepare your Dockerfile

The MLCube will execute a docker image whose entrypoint is `mlcube.py`. The MLCube will first build this image from the `Dockerfile` specified in the `project` folder. You can customize the Dockerfile however you want **as long as the entrypoint is runs the `mlcube.py` file**

Make sure you include in your Dockerfile any system dependency your code depends on. It is also common to have `pip` dependencies, make sure you install them in the Dockerfile as well.

Below is the docker file provided in the template:

``` dockerfile title="Dockerfile"
--8<-- "examples/chestxray/model_custom_cnn/project/Dockerfile"
```

As shown above, this docker file makes sure `python` is available by using the python base image, installs `pip` dependencies using the `requirements.txt` file, and sets the entrypoint to run `mlcube.py`. Note that the MLCube tool will invoke the Docker `build` command from the `project` folder, so it will copy all your files found in the `project` to the Docker image.

### The `mlcube` folder

This folder is mainly for configuring your MLCube and providing additional files the MLCube may interact with, such as parameters or model weights.

#### Include additional input files

##### parameters

Your inference logic may depend on some parameters (e.g. inference batch size). It is usually a more favorable design to not hardcode such parameters, but instead pass them when running the MLCube. This can be done by having a `parameters.yaml` file as an input to the MLCube. This file will be available to the `infer` command described before. You can parse this file in the `mlcube.py` file and pass its contents to your code.

This file should be placed in the `mlcube/workspace` folder.

##### model weights

It is a good practice not to ship your model weights within the docker image to reduce the image size and provide flexibility of running the MLCube with different model weights. To do this, model weights path should be provided as a separate parameter to the MLCube. You should place your model weights in a folder named `additional_files` inside the `mlcube/workspace` folder. This is how MedPerf expects any additional input to your MLCube beside the data path and the paramters file.

After placing your model weights in `mlcube/workspace/additional_files`, you have to modify two files:

- `mlcube.py`: add an argument to the `infer` command which will correspond to the path of your model weights. Remember also to pass this argument to your inference logic.
- `mlcube.yaml`: The next section introduces this file and describes it in details. You should add your extra input arguments to this file as well, as described below.

#### Configure your MLCube

The `mlcube.yaml` file contains metadata and configuration of your mlcube. This file was already populated with the configuration you provided during the step of creating the template. There is no need to edit anything in this file except if you are specifying extra parameters to the `infer` command (e.g. model weights as described in the previous section).

You will be modifying the `tasks` section of the `mlcube.yaml` file in order to account for extra additional inputs:

```yaml title="mlcube.yaml"
--8<-- "docs/snippets/model_mlcube/mlcube.yaml:17:29"
```

As hinted by the comments as well, you can add the additional parameters by specifying an extra key-value pair in the `inputs` dictionary of the `infer` task.

## Build your MLCube

After you follow the previous sections, the MLCube is ready to be built and run. Run the command below to build the MLCube. Make sure you are in the folder `model_mlcube/mlcube`.

```bash
mlcube configure -Pdocker.build_strategy=always
```

This command will build your docker image and make the MLCube ready to use.

## Run your MLCube

MedPerf will take care of running your MLCube. However, it's recommended to test the MLCube alone before using it with MedPerf for better debugging.

Use the command below to run the MLCube. Make sure you are in the folder `model_mlcube/mlcube`.

```bash
mlcube run --task infer data_path=<absolute path to input data> output_path=<absolute path to a folder where predictions will be saved>
```

## A Working Example

Assume you have the codebase below. This code can be used to predict thoracic diseases based on Chest X-ray data. The classification task is modeled as a multi-label classification class.

??? note "models.py"
    ```python

    --8<-- "examples/chestxray/model_custom_cnn/project/models.py"
    ```

??? note "data_loader.py"
    ```python

    --8<-- "examples/chestxray/model_custom_cnn/project/data_loader.py"
    ```

??? note "infer.py"
    ```python

    --8<-- "docs/snippets/model_mlcube/infer_unorganized.py"
    ```

Throughout the next sections, this code will be wrapped within an MLCube.

### Before Building the MLCube

The guidlines listed previously in [this section](#before-building-the-mlcube) will now be applied to the given codebase. Assume that you were instructed by the benchmark you are participating with to have your MLCube interface as follows:

- The MLCube should expect the input data folder to contain a list of images as numpy files.
- The MLCube should save the predictions in a single JSON file as key-value pairs of image file ID and its corresponding prediction. A prediction should be a vector of length 14 (number of classes) and has to be the output of the Sigmoid activation layer.

It is important to make sure that your MLCube will output an expected predictions format and consume a defined data format, since it will be used in a benchmarking pipeline whose data input is fixed and whose metrics calculation logic expects a fixed predictions format.

Considering the codebase above, here are the things that should be done before proceeding to build the MLCube:

- `infer.py` only prints predictions but doesn't store them. This has to be changed.
- `infer.py` hardcodes some parameters (`num_classes`, `in_channels`, `batch_size`) as well as the path to the trained model weights. Consider making these items configurable parameters. (This is optional but recommended)
- Consider refactoring `infer.py` to be a function so that is can be easily called by `mlcube.py`.

The other files `models.py` and `data_loader.py` seem to be good already. The data loader expects a folder containing a list of numpy arrays, as instructed.

Here is the modified version of `infer.py` according to the points listed above:

??? note "infer.py (Modified)"
    ```python hl_lines="10 11 12 13 17 35 36 37 38"

    --8<-- "examples/chestxray/model_custom_cnn/project/infer.py"
    ```

### Create an MLCube Template

Assuming you installed MedPerf, run the following:

```bash
medperf mlcube create model
```

You will be prompted to fill in the configuration options:

```bash
project_name [Model MLCube]: Custom CNN Classification Model
project_slug [model_mlcube]: model_custom_cnn
description [Model MLCube Template. Provided by MLCommons]: MedPerf Tutorial - Model MLCube.
author_name [John Smith]: <use your name>
accelerator_count [0]: 0
docker_image_name [docker/image:latest]: repository/model-tutorial:0.0.0
```

!!! note
    This example is built to be used with a CPU. See the [last section](#using-the-example-with-gpus) to know how to configure this example with a GPU.

Note that `docker_image_name` is arbitrarily chosen. Use a valid docker image.

### Move your Codebase

Move the three files of the codebase to the `project` folder. The directory tree will then look like this:

```bash hl_lines="10 11 12"
.
└── model_custom_cnn
    ├── mlcube
    │   ├── mlcube.yaml
    │   └── workspace
    │       └── parameters.yaml
    └── project
        ├── Dockerfile
        ├── mlcube.py
        ├── models.py
        ├── data_loader.py
        ├── infer.py
        └── requirements.txt
```

### Add your parameters and model weights

Since `num_classes`, `in_channels`, and `batch_size` are now parametrized, they should be defined in `workspace/parameters.yaml`. Also, the model weights should be placed inside `workspace/additional_files`.

#### Add parameters

Modify `parameters.yaml` to include the following:

```yaml title="parameters.yaml"
--8<-- "examples/chestxray/model_custom_cnn/mlcube/workspace/parameters.yaml"
```

#### Add model weights

Download the following model weights to use in this example: [Click here to Download]({{page.meta.weights_url}})

Extract the file to `workspace/additional_files`. The directory tree should look like this:

```bash hl_lines="6 7"
.
└── model_custom_cnn
    ├── mlcube
    │   ├── mlcube.yaml
    │   └── workspace
    │       ├── additional_files
    │       │   └── cnn_weights.pth
    │       └── parameters.yaml
    └── project
        ├── Dockerfile
        ├── mlcube.py
        ├── models.py
        ├── data_loader.py
        ├── infer.py
        └── requirements.txt
```

### Modify `mlcube.py`

Next, the inference logic should be triggered from `mlcube.py`. The `parameters_file` will be read in `mlcube.py` and passed as a dictionary to the inference logic. Also, an extra parameter `weights` is added to the function signature which will correspond to the model weights path. See below the modified `mlcube.py` file.

??? note "mlcube.py (Modified)"
    ```python hl_lines="3 5 15 17 18 19 20"

    --8<-- "examples/chestxray/model_custom_cnn/project/mlcube.py"
    ```

### Prepare the Dockerfile

The provided Dockerfile in the template is enough and preconfigured to download `pip` dependencies from the `requirements.txt` file. All that is needed is to modify the `requirements.txt` file to include the project's pip dependencies.

```txt title="requirements.txt"
--8<-- "examples/chestxray/model_custom_cnn/project/requirements.txt"
```

### Modify `mlcube.yaml`

Since the extra parameter `weights` was added to the `infer` task in `mlcube.py`, this has to be reflected on the defined MLCube interface in the `mlcube.yaml` file. Modify the `tasks` section to include an extra input parameter: `weights: additional_files/cnn_weights.pth`.

!!! tip
    The MLCube tool interprets these paths as relative to the `workspace`.

The `tasks` section will then look like this:

```yaml title="mlcube.yaml" hl_lines="9"
--8<-- "examples/chestxray/model_custom_cnn/mlcube/mlcube.yaml:17:27"
```

### Build your MLCube

Run the command below to create the MLCube. Make sure you are in the folder `model_custom_cnn/mlcube`.

```bash
mlcube configure -Pdocker.build_strategy=always
```

This command will build your docker image and make the MLCube ready to use.

!!! tip
    Run `docker image ls` to see your built Docker image.

### Run your MLCube

Download a sample data to run on: [Click here to Download]({{page.meta.data_url}})

Extract the data. You will get a folder `sample_prepared_data` containing a list chest X-ray images as numpy arrays.

Use the command below to run the MLCube. Make sure you are in the the folder `model_custom_cnn/mlcube`.

```bash
mlcube run --task infer data_path=<absolute path to `sample_prepared_data`> output_path=<absolute path to a folder where predictions will be saved>
```

## Using the Example with GPUs

The provided example codebase runs only on CPU. You can modify it to have `pytorch` run inference on a GPU.

The general instructions for building an MLCube to work with a GPU are the same as the provided instructions, but with the following slight modifications:

- Use a number different than `0` for the `accelerator_count` that you will be prompted with when creating the MLCube template.
- Make sure you install the required GPU dependencies in the docker image. For instance, this may be done by simply modifying the `pip` dependencies in the `requirements.txt` file to download `pytorch` with cuda.

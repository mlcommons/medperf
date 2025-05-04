# Creating a GaNDLF MLCube

## Overview

This guide will walk you through how to wrap a model trained using [GaNDLF](https://mlcommons.github.io/GaNDLF/){target="\_blank"} as a MedPerf-compatible MLCube ready to be used for **inference** (i.e. as a [Model MLCube](mlcube_models.md)). The steps can be summarized as follows:

1. Train a GaNDLF model
2. Create the MLCube file
3. (Optional) Create a custom entrypoint
4. Deploy the GaNDLF model as an MLCube

Before proceeding, make sure you have [medperf installed](../getting_started/installation.md) and [GaNDLF installed](https://mlcommons.github.io/GaNDLF/setup/).

## Before We Start

#### Download the Necessary files

A script is provided to download all the necessary files so that you follow the tutorial smoothly. Run the following: (make sure you are in MedPerf's root folder)

```bash
sh tutorials_scripts/setup_GaNDLF_mlcube_tutorial.sh
```

This will create a workspace folder `medperf_tutorial` where all necessary files are downloaded. Run `cd medperf_tutorial` to switch to this folder.

## 1. Train a GaNDLF Model

Train a small GaNDLF model to use for this guide. You can skip this step if you already have a trained model.

Make sure you are in the workspace folder `medperf_tutorial`. Run:

```bash
gandlf_run \
  -c ./config_getting_started_segmentation_rad3d.yaml \
  -i ./data.csv \
  -m ./trained_model_output \
  -t True \
  -d cpu
```

Note that if you want to train on GPU you can use `-d cuda`, but the example used here should take only few seconds using the CPU.

!!! warning
    This tutorial assumes the user is using the latest GaNDLF version. The configuration file `config_getting_started_segmentation_rad3d.yaml` will cause problems if you are using a different version, make sure you do the necessary changes.

You will now have your trained model and its related files in the folder `trained_model_output`. Next, you will start learning how to wrap this trained model within an MLCube.

## 2. Create the MLCube File

MedPerf provides a cookiecutter to create an MLCube file that is ready to be consumed by `gandlf_deploy` and produces an MLCube ready to be used by MedPerf. To create the MLCube, run: (make sure you are in the workspace folder `medperf_tutorial`)

```bash
medperf mlcube create gandlf
```

{% include "mlcubes/shared/cookiecutter.md" %}

You will be prompted to customize the MLCube creation. Below is an example of how your response might look like:

```bash
project_name [GaNDLF MLCube]: My GaNDLF MLCube # (1)!
project_slug [my_gandlf_mlcube]: my_gandlf_mlcube # (2)!
description [GaNDLF MLCube Template. Provided by MLCommons]: GaNDLF MLCube implementation # (3)!
author_name [John Smith]: John Smith # (4)!
accelerator_count [1]: 0 # (5)!
docker_build_file [Dockerfile-CUDA11.6]: Dockerfile-CPU # (6)!
docker_image_name [docker/image:latest]: johnsmith/gandlf_model:0.0.1 # (7)!
```

1. Gives a Human-readable name to the MLCube Project.
2. Determines how the MLCube root folder will be named.
3. Gives a Human-readable description to the MLCube Project.
4. Documents the MLCube implementation by specifying the author. Please use your own name here.
5. Indicates how many GPUs should be visible by the MLCube.
6. Indicates the Dockerfile name from GaNDLF that should be used for building your docker image. Use the name of the Dockerfile that aligns with your model's dependencies. Any "Dockerfile-*" in the [GaNDLF source repository](https://github.com/mlcommons/GaNDLF) is valid.
7. MLCubes use containers under the hood. Medperf supports both Docker and Singularity. Here, you can provide an image tag to the image that will be created by this MLCube. **It's recommended to use a naming convention that allows you to upload it to Docker Hub.**

Assuming you chose `my_gandlf_mlcube` as the project slug, you will find your MLCube created under the folder `my_gandlf_mlcube`. Next, you will use a `GaNDLF` utility to build the MLCube.

!!! note
    You **might** need to specify additional configurations in the `mlcube.yaml` file if you are using a GPU. Check the generated `mlcube.yaml` file for more info, as well as the [MLCube documentation](https://mlcommons.github.io/mlcube/).

## 3. (Optional) Create a Custom Entrypoint

When deploying the GaNDLF model directly as a model MLCube, the default entrypoint will be `gandlf_run ...`. You can override the entrypoint with a custom python script. One of the usecases is described below.

`gandlf_run` expects a `data.csv` file in the input data folder, which describes the inference test cases and their associated paths (Read more about GaNDLF's csv file conventions [here](https://mlcommons.github.io/GaNDLF/usage/#constructing-the-data-csv)). In case your MLCube will expect a data folder with a predefined data input structure but without this csv file, you can use a custom script that prepares this csv file as an entrypoint. You can find the recommended template and an example [here](https://github.com/mlcommons/GaNDLF/tree/master/mlcube/model_mlcube/example_custom_entrypoint).

## 4. Deploy the GaNDLF Model as an MLCube

To deploy the GaNDLF model as an MLCube, run the following: (make sure you are in the workspace folder `medperf_tutorial`)

```bash
gandlf_deploy \
  -c ./config_getting_started_segmentation_rad3d.yaml \
  -m ./trained_model_output \
  --target docker \
  --mlcube-root ./my_gandlf_mlcube \
  -o ./built_gandlf_mlcube \
  --mlcube-type model \
  --entrypoint <(optional) path to your custom entrypoint script> \ # (1)!
  -g False # (2)!
```

1. If you are not using a custom entrypoint, ignore this option.
2. Change to `True` if you want the resulting MLCube to use a GPU for inference.

GaNDLF will use your initial MLCube configuration `my_gandlf_mlcube`, the GaNDLF experiment configuration file `config_classification.yaml`, and the trained model `trained_model_output` to create a ready MLCube `built_gandlf_mlcube` and build the docker image that will be used by the MLCube. The docker image will have the model weights and the GaNDLF experiment configuration file embedded. You can check that your image was built by running `docker image ls`. You will see `johnsmith/gandlf_model:0.0.1` (or whatever image name that was used) created moments ago.

## 5. Next Steps

That's it! You have built a MedPerf-compatible MLCube with GaNDLF. You may want to submit your MLCube to MedPerf, you can follow [this tutorial](../getting_started/model_owner_demo.md).

!!! tip
    MLCubes created by GaNDLF have the model weights and configuration file embedded in the docker image. When you want to [deploy your MLCube for MedPerf](../concepts/mlcube_files.md), all you need to do is pushing the docker image and [hosting the mlcube.yaml file](../concepts/hosting_files.md).

## Cleanup (Optional)

You have reached the end of the tutorial! If you are planning to rerun any of the tutorials, don't forget to cleanup:

- To cleanup the downloaded files workspace (make sure you are in the MedPerf's root directory):

```bash
rm -fr medperf_tutorial
```

## See Also

- [Creating a Model MLCube from scratch.](mlcube_models.md)

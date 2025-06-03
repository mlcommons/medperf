# Containers in MedPerf

A [benchmark workflow](../workflow.md#step-2-register-benchmark) is composed of three steps: data preparation, inference, and metrics evaluation. These three steps are defined as containers. This document explains how to create these containers so that MedPerf is able to execute them properly.

## Container types

### Data Preparator Container

The Data Preparator container is used to prepare the data for executing the benchmark. Ideally, it can receive different data standards for the task at hand, transforming them into a single, unified standard. Additionally, it ensures the quality and compatibility of the data and computes statistics and metadata for registration purposes.

This container interface should expose the following tasks/entrypoints:

- **prepare:** Transforms the input data into the expected output data standard. It receives as input the location of the original data, as well as the location of the labels, and outputs the prepared dataset and accompanying labels. By default, inside the container filesystem, the container should read the input data from `/mlcommons/volumes/raw_data` and the input labels from `/mlcommons/volumes/raw_labels`, and should write the prepared/preprocessed version of the data in `/mlcommons/volumes/data` and `mlcommons/volumes/labels`.

- **sanity_check:** Ensures the integrity of the prepared data. It may check for anomalies and data corruption (e.g. blank images, empty test cases). It constitutes a set of conditions the prepared data should comply with. By default, inside the container filesystem, the container should read the input prepared data from `/mlcommons/volumes/data` and the input prepared labels from `/mlcommons/volumes/labels`.

- **statistics:** Computes statistics on the prepared data. By default, inside the container filesystem, the container should read the input prepared data from `/mlcommons/volumes/data` and the input prepared labels from `/mlcommons/volumes/labels`, and should write the computed statistics in the following file `/mlcommons/volumes/statistics/statistics.yaml`.

### Model Container

The model container contains a pre-trained machine learning model that is going to be evaluated by the benchmark. It's interface should expose the following task:

- **infer:** Runs inference and computes predictions on the prepared data. It receives as input the location of the prepared data and outputs the predictions. By default, inside the container filesystem, the container should read the input prepared data from `/mlcommons/volumes/data` and should write the predictions in `/mlcommons/volumes/predictions`.

### Metrics/Evaluator Container

The Metrics Container is used for computing metrics on the model predictions by comparing them against the ground truth labels. It's interface should expose the following task:

- **evaluate:** Computes the metrics. It receives as input the location of the predictions and the location of the prepared data labels and generates a yaml file containing the metrics. By default, inside the container filesystem, the container should read the input predictions from `/mlcommons/volumes/predictions` and the input prepared labels from `/mlcommons/volumes/labels`, and should write the computed metrics in the following file `/mlcommons/volumes/results/results.yaml`.

## Extra mounts

When creating a container, you may want to separate some assets from the container main code (e.g., your model weights, your model hyperparameters, some model weights used for annotation during data preparation, ...). MedPerf has a notion of an `additional_files` folder and a `parameters` file. When you submit a container metadata to the MedPerf server, you can put these assets inside a compressed folder `additional_files.tar.gz` file, and/or you can write your parameters to a `parameters.yaml` file. Then host these files and provide their URLs when submitting the container metadata. Instead of being baked inside the docker image, the contents of the archive `additional_files.tar.gz` file and the contents of the `parameters.yaml` file will be mounted by MedPerf to your container during runtime when your container is executed, as follows:

- **Additional files:** The contents of the `additional_files.tar.gz` archive will be uncompressed and available in `/mlcommons/volumes/additional_files` inside the container.
- **Parameters file:** Your parameters file will be available as `/mlcommons/volumes/parameters/parameters.yaml` inside the container.

## Container configuration file

A container configuration file defines properties about your container:

- Container type (Docker or Singularity)
- Image identifier (e.g., Dockerhub identifier for docker images, a URL to a .sif file for singularity images)
- Defined tasks. For example, if you are building a model container, it should define a `infer` task.
- For each defined task, you can specify run arguments (e.g., `command`, `environment variables`, ...) similar to how `docker run` consumes run arguments.
- For each defined task, the volumes to be mounted inside the container filesystem are configured.

You can get a template of the container config of each container type by using the `medperf container create` command, or by checking the examples in the repository.

### Customizing mount paths

By default, as mentioned in previous sections, MedPerf mounts input and output volumes to default paths inside the container (e.g., input data to a model container will be mounted at `/mlcommons/volumes/data`). You can customize where these mounts will appear inside the container by modifying the container configuration file. Note that these mount paths should be absolute paths.

### Restrictions

- Containers will not have network access during runtime. Any download or upload attempt inside the container during running it will result in an error.

- Containers will be run as a non-root user. Creating files and folders in the container filesystem outside the mounted predictions folder and outside the `/tmp` folder will result in permission error by default (unless you change filesystem permissions when building the container).

- Input volumes are mounted as read-only. Attempting to modify or delete them will result in an error.

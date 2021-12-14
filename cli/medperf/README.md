# MedPerf CLI
MedPerf provides a Command Line Interface for preparing local datasets and executing benchmarks on those datasets.This CLI is only required for Data Owners.

## Installation:
```
git clone https://github.com/mlcommons/medperf
cd medperf/cli
pip install .
```

## Quickstart:
MedPerf CLI interfaces with the server to be able to retrieve benchmarks and models, as well as upload dataset registrations and benchmark results from local datasets. Because of this, it is required to authenticate the CLI with the server. This can be done with the following command

```
medperf login
```

You can always override your previous authentication credentials by executing the login step at any time.

Once authenticated, you can start using the other commands provided.

- ### __Dataset Preparation__:
    Generates a version of a locally stored dataset for a specified benchmark. It requires three parameters:
    - Benchmark UID (`-b`, `--benchmark`): The Unique ID of the benchmark to prepare data for
    - Dataset Path (`-d`, `--data_path`): The location where data can be found
    - Labels Path (`-l`, `--labels_path`): The file that contains the labels for the specified dataset

    __Example__:
    ```
    medperf prepare -b <benchmark_uid> -d /path/to/dataset -l /path/to/labels
    ```
- ### __List Local Datasets__:
    Displays a table with information about the locally prepared datasets, including:
    - UID: The Unique ID used to register the dataset
    - Name: The name provided to the dataset upon registration
    - Data Preparation Cube UID: The Unique ID of the cube that prepared the dataset

    __Example__:
    ```
    medperf datasets
    ```
- ### __Benchmark Execution__:
    Executes a benchmark flow for a specific localle prepared dataset. It requires three parameters:
    - Benchmark UID (`-b`, `--benchmark`): The Unique ID of the benchmark to execute
    - Dataset UID (`-d`, `--data_uid`): The Unique ID of the prepared dataset
    - Model UID (`-m`, `--model_uid`): The Unique ID of the model to execute as part of the benchmark

    __Example__:
    ```
    medperf execute -b <benchmark_uid> -d <dataset_uid> -m <model_uid>
    ```
- ### __Dataset Association__:
    Creates an association request between a registered dataset and a specific benchmark. It requires two parameters:
    - Dataset UID (`-d`, `--data_uid`): The Unique ID of the prepared dataset
    - Benchmark UID (`-b`, `--benchmark_uid`): The Unique ID of the benchmark

    __Example__:
    ```
    medperf associate -d <dataset_uid> -b <benchmark_uid>
    ```
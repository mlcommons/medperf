# Medperf CLI
The Medperf CLI is a command-line-interface that provides tools for preparing datasets and executing benchmarks on such datasets.

## How to install:
Clone this repo
```
git clone https://github.com/mlcommons/medperf.git
```
Go to the `cli` folder
```
cd cli
```
Install using pip
```
pip install -e .
```

## How to run
The CLI provides the following commands:
- `login`: authenticates the CLI with the medperf backend server
  ```
  medperf login
  ```
- `dataset ls`: Lists all registered datasets by the user
  ```
  medperf dataset ls
  ```
- `dataset create`: Prepares a raw dataset for a specific benchmark
  ```
  medperf dataset create -b <BENCHMARK_UID> -d <DATA_PATH> -l <LABELS_PATH>
  ```
- `dataset submit`: Submits a prepared local dataset to the platform.
  ```
  medperf dataset submit -d <DATASET_UID> 
  ```
- `dataset associate`: Associates a prepared dataset with a specific benchmark
  ```
  medperf associate -b <BENCHMARK_UID> -d <DATASET_UID>
  ```
- `run`: Alias for `result create`. Runs a specific model from a benchmark with a specified prepared dataset
  ```
  medperf run -b <BENCHMARK_UID> -d <DATASET_UID> -m <MODEL_UID>
  ```
- `result ls`: Displays all results created by the user
  ```
  medperf result ls
  ```
- `result create`: Runs a specific model from a benchmark with a specified prepared dataset
  ```
  medperf result create -b <BENCHMARK_UID> -d <DATASET_UID> -m <MODEL_UID>
  ```
- `result submit`: Submits already obtained results to the platform
  ```
  medperf result submit -b <BENCHMARK_UID> -d <DATASET_UID> -m <MODEL_UID>
  ```
The CLI runs MLCubes behind the scene. This cubes require a container engine like docker, and so that engine must be running before running commands like `prepare` and `execute`
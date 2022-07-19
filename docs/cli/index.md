# Medperf CLI
The Medperf CLI is a command-line-interface that provides tools for interacting with the medperf platform, preparing datasets and executing benchmarks on such datasets.

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

### Login: 

authenticates the CLI with the medperf backend server

```
medperf login
```

### List Datasets: 

Lists all registered datasets by the user
  
```
medperf dataset ls
```

### Create Dataset: 

Prepares a raw dataset for a specific benchmark

```
medperf dataset create -b <BENCHMARK_UID> -d <DATA_PATH> -l <LABELS_PATH>
```

### Submit Dataset: 

Submits a prepared local dataset to the platform.
  
```
medperf dataset submit -d <DATASET_UID> 
```

### Associate Dataset: 

Associates a prepared dataset with a specific benchmark
  
```
medperf associate -b <BENCHMARK_UID> -d <DATASET_UID>
```

### Run a benchmark: 
Alias for `result create`: Runs a specific model from a benchmark with a specified prepared dataset
  
```
medperf run -b <BENCHMARK_UID> -d <DATASET_UID> -m <MODEL_UID>
```

### List Results: 

Displays all results created by the user
  
```
medperf result ls
```

### Create Result: 

Runs a specific model from a benchmark with a specified prepared dataset
  
```
medperf result create -b <BENCHMARK_UID> -d <DATASET_UID> -m <MODEL_UID>
```

### Submit Result: 

Submits already obtained results to the platform
  
```
medperf result submit -b <BENCHMARK_UID> -d <DATASET_UID> -m <MODEL_UID>
```

### List MLCubes: 

Lists all mlcubes created by the user. Lists all mlcubes if `--all` is passed
  
```
medperf mlcube ls [###-all]
``` 

### Submit MLCube: 

Submits a new mlcube to the platform
  
```
medperf mlcube submit
```   

### Associate MLCube: 

Associates an MLCube to a benchmark

```
medperf mlcube associate -b <BENCHMARK_UID> -m <MODEL_UID>
``` 

The CLI runs MLCubes behind the scene. These cubes require a container engine like docker, and so that engine must be running before running commands like `dataset create` or `result create`
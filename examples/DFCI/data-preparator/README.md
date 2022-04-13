# DFCI Data Preparator
This is a UNET implementation, following the structure and conventions MedPerf uses to process and transform raw datasets.

## Purpose:
Data Preparators are in charge of standardizing the input data format models expect to receive. Additionally, they provide tools for testing the integrity of the data and for extracting useful insights from it.

## How to run:
This template was built so it can work out-of-the-box. Follow the next steps:

1. Clone the repository
2. cd to the repository
   ```bash
   cd mlcube_examples
   ```
3. Install mlcube and mlcube-docker

   ```bash
   pip install mlcube mlcube-docker
   ```
4. cd to current example's `mlcube` folder

   ```bash
   cd medperf/data_preparator/mlcube
   ```
5. execute the `prepare` task with mlcube
   ```bash
   mlcube run --task=prepare
   ```
6. check resulting data
   ```bash
   ls workspace/data
   ```
7. execute the `sanity_check` task
    ```bash
    mlcube run --task=sanity_check
    ```
8. execute the `statistics` task
    ```bash
    mlcube run --task=statistics
    ``` 
9. check the resulting statistics
    ```bash
    cat workspace/statistics.yaml
    ```

## Contents

MLCubes usually share a similar folder structure and files. Here's a brief description of the role for the relevant files

1. __`mlcube/mlcube.yaml`__: 

    The `mlcube.yaml` file contains metadata about your data preparation procedure, including its interface. For MedPerf, we require three tasks: `prepare`, `sanity_check` and `statistics`. The description of the tasks and their input/outputs are described in the file:

    ```yml
    tasks:
        prepare:
        # This task is in charge of transforming the input data into the format
        # expected by the model cubes. 
            parameters:
            inputs: {
                data_path: images/,            # Required. Value must point to a directory containing the raw data inside workspace
                labels_path: labels/,         # Required. Value must point to a directory containing labels for the data
                parameters_file: parameters.yaml # Required. Value must be `parameters.yaml`
            }
            outputs: {
                output_path: data/               # Required. Indicates where to store the transformed data. Must contain transformed data and labels
            }
        sanity_check:
        # This task ensures that the previously transformed data was transformed correctly.
        # It runs a set of tests that check que quality of the data. The rigurosity of those
        # tests is determined by the cube author.
            parameters:
            inputs: {
                data_path: data/,                # Required. Value should be the output of the prepare task
                parameters_file: parameters.yaml # Required. Value must be `parameters.yaml`
            }
        statistics:
        # This task computes statistics on the prepared dataset. Its purpose is to get a high-level
        # idea of what is contained inside the data, without providing any specifics of any single entry
            parameters:
            inputs: {
                data_path: data/,                # Required. Value should be the output of the prepare task
                parameters_file: parameters.yaml # Required. Value must be `parameters.yaml`
            }
            outputs: {
                output_path: {
                type: file, default: statistics.yaml # Required. Value must be `statistics.yaml`
                }
            }
    ```

2. __`mlcube/workspace/parameters.yaml`__:

   This file provides ways to parameterize the data preparation process. You can set any key-value pairs that should be easily modifiable in order to adjust you mlcube's behavior. This file is mandatory, but can be left blank if parametrization is not needed, as is the case in this example.

3. __`project`__: 
   
   Contains the actual implementation of the mlcube. This includes all project-specific code, `Dockerfile` for building docker containers of the project and requirements for running the code.
    
5. __`project/mlcube.py`__:
   
   MLCube expects an entrypoint to the project in order to run the code and the specified tasks. It expects this entrypoint to behave like a CLI, in which each MLCube task (e.g. `prepare`) is executed as a subcommand, and each input/output parameter is passed as a CLI argument. An example of the expected interface is:
   ```bash
    python3 project/mlcube.py prepare --data_path=<DATA_PATH>  --labels_path=<LABELS_PATH> --parameters_file=<PARAMETERS_FILE> --output_path=<OUTPUT_PATH>
   ```
   `mlcube.py` provides such interface for this toy example. As long as you follow such CLI interface, you can implement it however you want. We provide an example that requirems minimal modifications to the original project code, by running any project task through subprocesses.


# MedPerf's Data Preparator MLCube Template
This is a Hello World implementation, following the structure and conventions MedPerf uses to process and transform raw datasets.

## Purpose:
At the time of writing, Data Preparators are in charge of standardizing the input data format models expect to receive. Additionally, they provide tools for testing the integrity of the data and for extracting useful insights from it.

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
That's it! You just built and ran a hello-world data preparator mlcube!

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
                data_path: names/,            # Required. Value must point to a directory containing the raw data inside workspace
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

## How to modify
If you want to adjust this template for your own use-case, then the following list serves as a step-by-step guide:
1. Remove demo artifacts from `/mlcube/workspace`: 
     - `/mlcube/workspace/data`
     - `/mlcube/workspace/labels`
     - `/mlcube/workspace/names`
     - `/mlcube/workspace/statistics.yaml`
2. Pass your original code to the `/project` folder (removing everything but `mlcube.py`) 
3. Adjust your code and the `/project/mlcube.py` file so that commands point to the respective code and receive the expected arguments
4. Modify `/project/requirements.txt` so that it contains all code dependencies for your project
5. Default `/project/Dockerfile` should suffice, but feel free to add/modify it to work with your needs. As long as it has an entrypoint pointing to `mlcube.py`
6. Inside `/mlcube/workspace` add the input folders for preparing data.
7. Inside `/mlcube/workspace/additional_files` add any files that are required for model execution (e.g. model weights)
8. Adjust `/mlcube/mlcube.yaml` so that:
   1. metadata such as `name`, `description`, `authors` and `image_name` are correctly assigned.
   2. `data_path`, `labels_path` and other IO parameters point to the location where you expect data to be inside the `workspace` directory.
   3. `parameters_file` should NOT be modified in any way.
   4. Add any other required parameters that point to `additional_files` (e.g. model_weights). Naming can be arbitrary, but all files referenced from now on should be contained inside `additional_files`.
   5. `output_path`s should NOT be modified in any way.

## Requirements are negotiable
The required fields in the mlcube task interface show what medperf currently assumes. As we are in alpha, this is a great time to raise concerns or requests about these requirements! Now is the best time for us to make changes.
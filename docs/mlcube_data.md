# Data Preparator MLCube
## Purpose
Data Preparators are in charge of standardizing the input data format models expect to receive. Additionally, they provide tools for testing the integrity of the data and extracting valuable insights from it.

## Hello World task
To provide a basic example of how Medperf MLCubes work under the hood, we provide a toy Hello World benchmark. This benchmark implements a pipeline for ingesting people's names, and generating greetings for those names given some criteria. Although this is not the most scientific example, it provides a clear idea of all the pieces that are required to implement your own MLCubes for Medperf.

You can find the Data Preparator MLCube code [here](https://github.com/mlcommons/medperf/examples/HelloWorld/data_preparator)

## How to run
Before we dig into the code, let's first try to manually run the Data Preparator MLCube:

1. Clone the repository.
    ```bash
    git clone https://github.com/mlcommons/medperf
    ```

2. Install mlcube and mlcube-docker using pip
    ```bash
    pip install mlcube mlcube-docker
    ```

3. Navigate to the HelloWorld directory within the examples folder with
    ```bash
    cd examples/HelloWorld
    ```

4. Change to the current example's `mlcube` folder with
    ```bash
    cd data_preparator/mlcube
    ```

5. Run the `prepare` task with the mlcube
    ```bash
    mlcube run --task=prepare
    ```

6. Check the resulting data using
    ```bash
    ls workspace/data
    ```

7. Run the `sanity_check` task with
     ```bash
     mlcube run --task=sanity_check
     ```

8. Run the `statistics` task using
    ```bash
    mlcube run --task=statistics
    ``` 

9.  Check the resulting statistics using the following command:
    ```bash
    cat workspace/statistics.yaml
    ```

That's it! You just built and ran a hello-world data preparator mlcube!

## Contents

MLCubes usually share similar folder and file structures. In this section we provide a brief description of the role for the relevant files.

### `mlcube/mlcube.yaml`

The `mlcube.yaml` file contains metadata about your data preparation procedure, including its interface. For MedPerf, we require three tasks: `prepare`, `sanity_check`, and `statistics`. The description of tasks and their input/outputs are described as follows:

``` yaml title="mlcube.yaml"
tasks:
    prepare: # (1)!
        parameters:
            inputs: {
                data_path: names, # (2)!
                labels_path: labels, # (3)!
                parameters_file: parameters.yaml, # (4)!
            }
            outputs:
                output_path: {type: directory, default: data} # (5)!
                # output_labels_path: {type: directory, default: output_labels} (6)

    sanity_check: # (7)!
        parameters:
            inputs: {
                data_path: data, # (8)!
                parameters_file: parameters.yaml # (9)!
            }

    statistics: # (10)!
        parameters:
            inputs: {
                data_path: data, # (11)!
                parameters_file: parameters.yaml # (12)!
            }
            outputs: {
                output_path: statistics.yaml # (13)!
            }
```

1. **Required**. The prepare task transforms the input data and labels into the format expected by model cubes
2. **Required**. Where to find the input raw data. **MUST** be a folder.
3. **Required**. Where to find the input labels. **MUST** be a folder.
4. **Required**. Helper file to provide additional arguments. Value **MUST** be `parameters.yaml`
5. **Required**. Where to store prepared data and labels. **MUST** be a folder
6. **Optional**. Where to store prepared labels. If not provided, labels should be stored with the prepared data.
7. **Required**. The sanity_check task verifies the quality of the transformed data. If the data does not pass quality check, the `sanity_check` task **MUST** throw an error.
8. **Required**. Where to find the prepared data. This is usually the output of the prepare task. **MUST** be a folder.
9. **Required**. Helper file to provide additional arguments. Value **MUST** be `parameters.yaml`
10. **Required**. The statistics task computes general statistics over the prepared data. This serves as a brief description of the data being prepared.
11. **Required**. Where to find the prepared data. This is usually the output of the `prepare` task. **MUST** be a folder.
12. **Required**. Helper file to provide additional arguments. Value **MUST** be `parameters.yaml`
13. **Required**. Where to store the statistics value. **MUST** be `statistics.yaml`

!!! note Separate labels output
    We provide an option to physically separate data and labels by defining the `output_labels_path` inside the `prepare` task. This is useful for challenges or benchmarks where model authors are not necessarily trusted. By doing this, the models won't be able to access any of the labels during the `infer` task.
---

### `mlcube/workspace/parameters.yaml`

   This file provides ways to parameterize the data preparation process. You can set any key-value pairs that should be easily modifiable to adjust your mlcube's behavior. This file is mandatory but can be left blank if parametrization is unnecessary, like in this example.

---

### `project`

   Contains the actual implementation of the mlcube, including all project-specific code, `Dockerfile` for building docker containers of the project, and requirements for running the code.

---
    
### `project/mlcube.py`
   
MLCube expects an entry point to the project to run the code and the specified tasks. It expects this entry point to behave like a CLI, in which each MLCube task (e.g., `prepare`) is executed as a subcommand – and each input/output parameter is passed as a CLI argument. 

``` bash
python3 project/mlcube.py prepare --data_path=<DATA_PATH>  --labels_path=<LABELS_PATH> --parameters_file=<PARAMETERS_FILE> --output_path=<OUTPUT_PATH>
```

`mlcube.py` provides an interface for this toy example. You can implement such a CLI interface with any language or tool as long as you follow the command structure demonstrated above. We provide an example that requires minimal modifications to the original project code by running any project task through subprocesses.

---

## How to modify
If you want to adjust this template for your own use case, then the following list serves as a step-by-step guide:

1. Remove demo artifacts from `/mlcube/workspace`: 
     - `/mlcube/workspace/data`
     - `/mlcube/workspace/labels`
     - `/mlcube/workspace/names`
     - `/mlcube/workspace/statistics.yaml`

2. Pass your original code to the `/project` folder, removing everything but `mlcube.py`.

3. Adjust your code and the `/project/mlcube.py` file so the commands point to the respective code and receive the expected arguments.

4. Modify `/project/requirements.txt` so that it contains all code dependencies for your project.

5. Default `/project/Dockerfile` should suffice. However, feel free to add/modify it to work with your needs as long as it has an entry point pointing to `mlcube.py`.

6. Inside `/mlcube/workspace`, add the input folders for preparing data.

7. Inside `/mlcube/workspace/additional_files`, add any files required for model execution (e.g., model weights).

8. In `/mlcube/mlcube.yaml`, make the following changes:
    1. Modify the metadata fields (e.g., `name`, `description`, `authors`, `image_name`) to the correct values.
    2. Set the `data_path`, `labels_path`, and other IO parameters to the appropriate locations within the `workspace` directory.
    3. **DO NOT** modify `parameters_file` in any way.
    4. Add any required parameters that point to additional_files (e.g., model_weights). These files should be contained inside additional_files, and the naming can be arbitrary.
    5. **DO NOT** modify the `output_path`s in any way.

!!! note "Requirements are negotiable"
    The fields required in the mlcube task interface are currently defined by the Medperf platform. We encourage users to raise any concerns or requests regarding these requirements while the platform is in alpha, as this is an ideal time to make changes. Please feel free to contact us with your feedback.

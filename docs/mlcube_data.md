# MedPerf's Data Preparator MLCube Template
This Hello World implementation follows the structure and conventions MedPerf uses to process and transform raw datasets.

## Purpose:
At the time of writing, Data Preparators are in charge of standardizing the input data format models expect to receive. Additionally, they provide tools for testing the integrity of the data and extracting valuable insights from it.

## How to run:
This template was built in a way it works out of the box. You can follow the next steps to get started:

1. Clone the repository
2. Navigate to the `mlcube_examples` directory within the repository
   ```bash
   cd mlcube_examples
   ```
3. Install mlcube and mlcube-docker using pip

   ```bash
   pip install mlcube mlcube-docker
   ```
4. Change to the current example's `mlcube` folder

   ```bash
   cd medperf/data_preparator/mlcube
   ```
5. Run the `prepare` task with the mlcube
   ```bash
   mlcube run --task=prepare
   ```
6. Check the resulting data
   ```bash
   ls workspace/data
   ```
7. Run the `sanity_check` task
    ```bash
    mlcube run --task=sanity_check
    ```
8. Run the `statistics` task
    ```bash
    mlcube run --task=statistics
    ``` 
9. Check the resulting statistics
    ```bash
    cat workspace/statistics.yaml
    ```
That's it! You just built and ran a hello-world data preparator mlcube!

## Contents

MLCubes usually share similar folder and file structures. Here's a brief description of the role for the relevant files

1. __`mlcube/mlcube.yaml`__: 

    The `mlcube.yaml` file contains metadata about your data preparation procedure, including its interface. For MedPerf, we require three tasks: `prepare`, `sanity_check`, and `statistics`. The description of tasks and their input/outputs are described as follows:

    ```yml
    tasks:
    prepare:
    # Transforms the input data and labels into the format expected by model cubes
    parameters:
        inputs:
            data_path:
                type: directory
                description: Directory containing the raw data
                required: true

            labels_path:
                type: directory
                description: Directory containing the labels for the data
                required: true

            parameters_file:
                type: file
                description: File containing additional arguments for the data transformation
                required: true
                default: "parameters.yaml" #Value must be as in default

        outputs:
            output_path:
                type: directory
                description: Directory to store the transformed data and labels
                required: true

    sanity_check:
    # Verifies the quality of the transformed data
        parameters:
        inputs:
            data_path:
                type: directory
                description: Directory containing the transformed data (output of the prepare task)
                required: true

            parameters_file:
                type: file
                description: File containing additional arguments for the sanity check
                required: true
                default: "parameters.yaml" #Value must be as in default

    statistics:
    # Computes statistics on the prepared dataset
        parameters:
        inputs:
            data_path:
                type: directory
                description: Directory containing the transformed data (output of the prepare task)
                required: true

            parameters_file:
                type: file
                description: File containing additional arguments for the statistics computation
                required: true
                default: "parameters.yaml" #Value must be as in default

        outputs:
            output_path:
                type: file
                description: File to store the computed statistics
                required: true
                default: "statistics.yaml" #Value must be as in default



    ```

2. __`mlcube/workspace/parameters.yaml`__:

   This file provides ways to parameterize the data preparation process. You can set any key-value pairs that should be easily modifiable to adjust your mlcube's behavior. This file is mandatory but can be left blank if parametrization is unnecessary, as in this example.

3. __`project`__: 
   
       Contains the actual implementation of the mlcube. This includes:
All project-specific code 
`Dockerfile` – for building docker containers of the project 
Requirements for running the code.
    
5. __`project/mlcube.py`__: 
   
   MLCube expects an entry point to the project to run the code and the specified tasks. It expects this entry point to behave like a CLI, in which each MLCube task (e.g., `prepare`) is executed as a subcommand – and each input/output parameter is passed as a CLI argument. 

   ```bash
    python3 project/mlcube.py prepare --data_path=<DATA_PATH>  --labels_path=<LABELS_PATH> --parameters_file=<PARAMETERS_FILE> --output_path=<OUTPUT_PATH>
   ```
   `mlcube.py` provides an interface for this toy example. You can implement such a CLI interface as long as you follow it. We provide an example that requires minimal modifications to the original project code by running any project task through subprocesses.

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
 Modify the metadata fields (e.g., `name`, `description`, `authors`, `image_name`) to the correct values.
Set the `data_path`, `labels_path`, and other IO parameters to the appropriate locations within the `workspace` directory.
Do NOT modify `parameters_file` in any way.
Add any required parameters that point to additional_files (e.g., model_weights). These files should be contained inside additional_files, and the naming can be arbitrary.
Do NOT modify the `output_path`s in any way.

## Requirements are negotiable
The fields required in the mlcube task interface are currently defined by the Medperf platform. We encourage users to raise any concerns or requests regarding these requirements while the platform is in alpha, as this is an ideal time to make changes. Please feel free to contact us with your feedback.

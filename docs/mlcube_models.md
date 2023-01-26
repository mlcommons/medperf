# MedPerf's Model MLCube Template
This document consists of a Hello World implementation, following the structure and conventions MedPerf uses to run Models on the platform successfully.

## Purpose:
At the time of writing, model MLCubes only obtain predictions on data, meaning that we expect all models inside MedPerf to be already trained. 

## How to run:
This template was built thought to work out of the box. Follow the next steps:

1. Clone the repository.
2. Change the current directory to the repository:

   ```bash
   cd mlcube_examples
   ```
3. Create and activate a virtual environment:
   ```bash
   conda create -n venv_mlcub python=3.7 -y # change to your prefered python version
   conda activate venv_mlcub
   ```
4. Install mlcube and mlcube-docker using pip:
   ```bash
   pip install mlcube mlcube-docker
   ```
5. Change the current directory to the `mlcube` folder within the `medperf/model` folder of the repository:
   ```bash
   cd medperf/model/mlcube
   ```
6. Run the `infer` task using mlcube:
   ```bash
   mlcube run --task=infer
   ```
7. View the resulting predictions by reading the `predictions.csv` file in the `workspace/predictions` folder:
   ```bash
   cat workspace/predictions/predictions.csv
   ```
That's it! You just built and ran a hello-world model mlcube!

## Contents

MLCubes usually share a similar folder structure and files. Here's a brief description of the role for the relevant files:

1. __`mlcube/mlcube.yaml`__: 
   
   The `mlcube.yaml` file in your project contains metadata about your model, including its interface. To use your model with MedPerf, the `mlcube.yaml` file must define an infer function that takes in at least two arguments: `data_path` and `parameters_file`, and produces prediction artifacts in the `output_path`. This definition can be found in the `mlcube.yaml` file as:

    ```yml
    tasks:
      # Model MLCubes require only a single task: `infer`.
      # This task takes input data, as well as configuration parameters
      # and/or extra artifacts, and generates predictions on the data
      infer:
         parameters:
            inputs: {
               data_path: data,                                    # Required. Where to find the data to run predictions on. MUST be a folder
               parameters_file: parameters.yaml,                   # Required. Helper file to provide additional arguments. Value MUST be parameters.yaml
               # If you need any additional files that should 
               # not be included inside the mlcube image, 
               # add them inside `additional_files` folder
               # E.g. model weights

               # Toy Hello World example
               greetings: additional_files/greetings.csv
            }
            outputs: {
               output_path: {type: directory, default: predictions} # Required. Where to store prediction artifacts. MUST be a folder
            }

    ```
    In this case, we’ve added an extra “greetings” argument to our infer function. Note that the default value will always be used.

2. __`mlcube/workspace/parameters.yaml`__:

   This file provides ways to parameterize your model. You can set any key-value pairs that should be easily modifiable to adjust your model's behavior. Current example shows a primary usage case for changing generated Hello world examples to uppercase:

   ```yml
    # Here you can store any key-value arguments that should be easily modifiable
    # by external users. E.g. batch_size

    # example argument for Hello World
    uppercase: false
   ```
   To perform inference on large volumes while conserving memory, you can enable patching by including the "patching" setting in your `parameters.yaml` file. You can register multiple "mlcubes" with different parameters to apply different parameter settings.yaml files. This allows you to customize the behavior of your model for different scenarios.

   Though we use the term “registering in mlcube”, really you register a mlcube and `parameters.yaml` file, such that you have separate registrations for different configurations of your cube. In this way, one registered “mlcube” might be your model with “patching: true”, and another might be “patching: false”. These two registered cubes share the same image file, and medperf/mlcube will re-use the downloaded image while downloading each parameter.yaml files. 

   In our example, we have implemented one cube and registered it twice, each with different `parameters.yaml ` files and our benchmark will now compare our model with patching against our model without patching.

3. __`mlcube/workspace/additional_files/*`__:
   
   Due to size or usability constraints, you may require additional files that should not be packaged inside the mlcube, like weights. For these cases, we provide an additional folder called `additional_files`. 

   Here, you can provide any other files that should be present during inference. At the time of mlcube registration, this folder must be compressed into a tarball `.tar.gz` and hosted somewhere on the web. 

   MedPerf will then be able to download, verify and reposition those files in the expected location for model execution. To reference such files, you can provide additional parameters to the `mlcube.yaml` task definition, as we demonstrate with the `greetings` parameter.



4. __`project`__: 
   
   Contains the actual implementation of the mlcube. This includes all project-specific code, `Dockerfile` for building docker containers of the project and requirements for running the code.

5. __`project/mlcube.py`__:
   
   MLCube expects an entry point to the project to run the code and the specified tasks. It expects this entry point to behave like a CLI, in which each MLCube task (e.g., `infer`) is executed as a subcommand – and each input/output parameter is passed as a CLI argument. 

   An example of the expected interface is:

   ```bash
    python3 project/mlcube.py infer --data_path=<DATA_PATH> --parameters_file=<PARAMETERS_FILE> --greetings=<GREETINGS_FILE> --output_path=<OUTPUT_PATH>
   ```

   `mlcube.py` provides an interface for this toy example. You can implement such a CLI interface as long as you follow it. We provide an example that requires minimal modifications to the original project code by running any project task through subprocesses.

   #### __What is that “hotfix” function I see in mlcube.py?__

   To summarize, this issue is benign and can be safely ignored. It prevents a potential issue with the CLI and does not require further action.

   If you use the typer/click library for your command-line interface (CLI) and have only one @app.command, the command line may not be parsed as expected by mlcube. This is due to a known issue that can be resolved by adding more than one task to the mlcube interface.
   
   To avoid a potential issue with the CLI, we add a dummy typer command to our model cubes that only have one task. If you're not using typer/click, you don't need this dummy command.

## How to modify

If you want to adjust this template for your own use case, then the following list serves as a step-by-step guide:
1. Remove the demo artifacts from the `/mlcube/workspace` folder:
`/mlcube/workspace/data/*`
`/mlcube/workspace/predictions/*`
`/mlcube/workspace/additional_files/greetings.csv`

2. Place your original code in the `/project folder`, removing `app.py`.
3. Adjust your code and the `/project/mlcube.py` file, so the commands point to the correct code and receive the expected arguments.
4. Modify /project/requirements.txt to include all code dependencies for your project.
5. The default `/project/Dockerfile ` should be sufficient, but you can modify it to meet your needs as long as it has an entry point pointing to `mlcube.py`.
6. Inside `/mlcube/workspace`, add the data you want your model to use for inference.
7. Inside `/mlcube/workspace/additional_files`, add any files required for model execution (e.g., `model weights`).
8. In `/mlcube/mlcube.yaml`, make the following changes:
1. Assign the correct values to the metadata fields (`name`, `description`, `authors`, `image_name`).
2. Set `data_path `to the location of the data inside the workspace directory.
3. Do NOT modify `parameters_file`.
4. Remove the demo `greetings `parameter.
5. Add any other required parameters that point to additional_files. The naming can be arbitrary, but all referenced files should be contained inside `additional_files`.
6. Do NOT modify `output_path`.


## Requirements are negotiable

The fields required in the mlcube task interface are currently defined by the Medperf platform. We encourage users to raise any concerns or requests regarding these requirements while the platform is in alpha, as this is an ideal time to make changes. Please feel free to contact us with your feedback.



# DFCI Model Cube 2

## Purpose:
At the time of writing, model MLCubes have the only purpose of obtaining predictions on data. This means that we expect all models inside MedPerf to already be trained. 

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
   cd medperf/model/mlcube
   ```
5. execute the `infer` task with mlcube
   ```bash
   mlcube run --task=infer -Pdocker.build_strategy=auto
   ```
6. check resulting predictions
   ```bash
   cat workspace/predictions/predictions.csv
   ```

## Contents

MLCubes usually share a similar folder structure and files. Here's a brief description of the role for the relevant files

1. __`mlcube/mlcube.yaml`__: 
   
   The `mlcube.yaml` file contains metadata about your model, including its interface. For MedPerf, we require an `infer` function that takes in (at minimum) arguments for `data_path` and `parameters_file` and produces prediction artifacts inside the `output_path`. You see this definition in the mlcube.yaml file as:

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
               greetings: additional_files/predictions.csv
            }
            outputs: {
               output_path: {type: directory, default: predictions} # Required. Where to store prediction artifacts. MUST be a folder
            }

    ```
    In this case, we’ve added an extra “greetings” argument to our infer function. Note that the default value will always be used.

   In real-case scenarios, you may want to enable various parameter settings in your model. For example, perhaps you want to enable patching for large volumes to save on memory consumption, where patches of the volume are inference and the outputs stitched together.  To do this, you would include something like “patching: …” in your parameters.yaml file, and then you would register multiple “mlcubes” with different parameters.yaml files. Though we use the term “registering in mlcube”, really you register an mlcube and a parameters.yaml file, such that you have separate registrations for different configurations of your cube. In this way, one registered “mlcube” might be your model with “patching: true”, and another might be “patching: false”. These two registered cubes would share the same image file, and medperf/mlcube will be smart about re-using the downloaded image while downloading each of the parameters.yaml files. In our example, we have implemented one cube, registered it twice, each with a different parameters.yaml file, and our benchmark will now compare our model with patching against our model without patching.

2. __`mlcube/workspace/additional_files/*`__:
   
   In this case, model parameters are stored in additional_files. 

3. __`project`__: 
   
   Contains the actual implementation of the mlcube. This includes all project-specific code, `Dockerfile` for building docker containers of the project and requirements for running the code.

4. __`project/mlcube.py`__:
   
   MLCube expects an entrypoint to the project in order to run the code and the specified tasks. It expects this entrypoint to behave like a CLI, in which each MLCube task (e.g. `infer`) is executed as a subcommand, and each input/output parameter is passed as a CLI argument. An example of the expected interface is:
   ```bash
    python3 project/mlcube.py infer --data_path=<DATA_PATH> --parameters_file=<PARAMETERS_FILE> --greetings=<GREETINGS_FILE> --output_path=<OUTPUT_PATH>
   ```
   `mlcube.py` provides such interface for this toy example. As long as you follow such CLI interface, you can implement it however you want. We provide an example that requirems minimal modifications to the original project code, by 
   running any project task through subprocesses.

   #### __What is that “hotfix” function I see in mlcube.py?__

    In short, it’s benign and there to avoid a potential cli issue, so you can just leave it and forget about it.

    For those who care, when using typer/click for your cli, like we do, you need more than one @app.command, or typer/click will not parse the command-line in the way mlcube expects. This is a silly, known issue that goes away as soon as you have more than one task in your mlcube interface. But since our model cubes currently only have one task, we add an extra, blank typer command to avoid this issue. If you don’t use typer/click, you likely don’t need this dummy command.

## How to modify
If you want to adjust this template for your own use-case, then the following list serves as a step-by-step guide:
1. Remove demo artifacts from `/mlcube/workspace`: 
     - `/mlcube/workspace/data/*`
     - `/mlcube/workspace/predictions/*`
     - `/mlcube/workspace/additional_files/full_unet.pth`
2. Pass your original code to the `/project` folder (removing `app.py`) 
3. Adjust your code and the `/project/mlcube.py` file so that commands point to the respective code and receive the expected arguments
4. Modify `/project/requirements.txt` so that it contains all code dependencies for your project
5. Default `/project/Dockerfile` should suffice, but feel free to add/modify it to work with your needs. As long as it has an entrypoint pointing to `mlcube.py`
6. Inside `/mlcube/workspace` add the data you want your model to use for inference
7. Inside `/mlcube/workspace/additional_files` add any files that are required for model execution (e.g. model weights)
8. Adjust `/mlcube/mlcube.yaml` so that:
   1. metadata such as `name`, `description`, `authors` and `image_name` are correctly assigned.
   2. `data_path` points to the location where you expect data to be inside the `workspace` directory.
   3. `parameters_file` should NOT be modified in any way.
   4. remove demo `greetings` parameter.
   5. Add any other required parameters that point to `additional_files` (e.g. model_weights). Naming can be arbitrary, but all files referenced from now on should be contained inside `additional_files`.
   6. `output_path` should NOT be modified in any way.

## Requirements are negotiable
The required fields in the mlcube task interface show what medperf currently assumes. As we are in alpha, this is a great time to raise concerns or requests about these requirements! Now is the best time for us to make changes.

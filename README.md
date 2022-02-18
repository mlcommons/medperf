# MedPerf

Medperf is an open benchmarking platform for medical artificial intelligence using Federated Evaluation.

## What's included here
Inside this repo you can find all important pieces for running MedPerf. In its current state, it includes:
- ### MedPerf Server:
  Backend server implemented in django. Can be found inside the `server` folder
- ### MedPerf CLI:
  Command Line Interface for interacting with the server. Can be found inside the `cli` folder.

## How to run
In order to run MedPerf locally, you must host the server in your machine, and install the CLI.

1. ## Install dependencies
   MedPerf has some dependencies that must be installed by the user before being able to run. This are mlcube and the required runners (right now there's docker and singularity runners). Depending on the runner you're going to use, you also need to download the runner engine. For this demo, we will be using Docker, so make sure to get the [Docker Engine](https://docs.docker.com/get-docker/)

   ```
   pip install mlcube mlcube-docker mlcube-singularity
   ```

2. ## Host the server:
    To host the server, please follow the instructions inside the [`server/README.md`](server/README.md) file.

3. ## Install the CLI:
   To install the CLI, please follow the instructions inside the [`cli/README.md`](cli/README.md) file.

## Demo
The server comes with prepared users and cubes for demonstration purposes. A toy benchmark was created beforehand for benchmarking XRay models. To execute it you need to:
1. ## Get the data
   The toy benchmark uses the [TorchXRayVision]() library behind the curtain for both data preparation and model implementations. To run the benchmark, you need to have a compatible dataset. The supported dataset formats are:
   - RSNA_Pneumonia
   - CheX
   - NIH
   - NIH_Google
   - PC
   - COVID19
   - SIIM_Pneumothorax
   - VinBrain
   - NLMTB

   As an example, we're going to use the CheXpert Dataset for the rest of this guide. You can get it [here](https://stanfordmlgroup.github.io/competitions/chexpert/). Even though you could use any version of the dataset, we're going to be using the downsample version for this demo. Once you retrieve it, keep track of where it is located on your system. For this demonstration, we're going to assume the dataset was unpacked to this location: 
   
   ```
   ~/CheXpert-v1.0-small
   ```
   We're going to be using the validation split
2. ## Authenticate the CLI
   If you followed the server hosting instructions, then your instance of the server already has some toy users to play with. The CLI needs to be authenticated with a user to be able to execute commands and interact with the server. For this, you can run:
   ```
   medperf login
   ```
   And provide `testdataowner` as user and `test` as password. You only need to authenticate once. All following commands will be authenticated with that user.
3. ## Run the data preparation step
   Benchmarks will usually require a data owner to generate a new version of the dataset that has been preprocessed for a specific benchmark. The command to do that has the following structure
   ```
   medperf dataset create -b <BENCHMARK_UID> -d <PATH_TO_DATASET> -l <PATH_TO_LABELS>
   ```
   for the CheXpert dataset, this would be the command to execute:
   ```
   medperf dataset create -b 1 -d ~/CheXpert-v1.0-small -l ~/CheXpert-v1.0-small/valid.csv
   ```
   Where we're executing the benchmark with UID `1`, since is the first and only benchmark in the server. By doing this, the CLI retrieves the data preparation cube from the benchmark and processes the raw dataset. You will be prompted for additional information and confirmations for the dataset to be prepared and registered onto the server.
4. ## Run the benchmark execution step
   Once the dataset is prepared and registered, you can execute the benchmark with a given model mlcube. The command to do this has the following structure
   ```
   medperf execute -b <BENCHMARK_UID> -d <DATA_UID> -m <MODEL_UID>
   ```
   For this demonstration, you would execute the following command:
   ```
   medperf execute -b 1 -d 1 -m 2
   ```
   Given that the prepared dataset was assigned the UID of 1. You can find out what UID your prepared dataset has with the following command:
   ```
   medperf dataset ls
   ```
   Additional models have been provided to the benchmark, this is the list of models you can execute:
   - 2: CheXpert DenseNet Model
   - 4: ResNet Model
   - 5: NIH DenseNet Model

    During model execution, you will be asked for confirmation of uploading the metrics results to the server.

## Automated Test
A `test.sh` script is provided for automatically running the whole demo on a public mock dataset.

### Requirements for running the test
- It is assumed that the `medperf` command is already installed (See instructions on `cli/README.md`) and that all dependencies for the server are also installed (See instructions on `server/README.md`).
- `mlcube` command is also required (See instructions on `cli/README.md`)
- The docker engine must be running
- A connection to internet is required for retrieving the demo dataset and mlcubes

Once all the requirements are met, running `sh test.sh` will:
- cleanup any leftover medperf-related files (WARNING! Running this will delete the medperf workspace, along with prepared datasets, cubes and results!)
- Instantiate and seed the server using `server/server.sh`
- Retrieve the demo dataset
- Run the CLI demo using `cli/cli.sh`
- cleanup temporary files
![image](https://user-images.githubusercontent.com/25375373/163279746-14d7902b-98ed-4fcf-a4e3-f27d4bcbd339.png)

# MedPerf

Medperf is an open benchmarking platform for medical artificial intelligence using Federated Evaluation.

## What's included here
Inside this repo you can find all important pieces for running MedPerf. In its current state, it includes:
- ### MedPerf Server:
  Backend server implemented in django. Can be found inside the `server` folder
- ### MedPerf CLI:
  Command Line Interface for interacting with the server. Can be found inside the `cli` folder.
- ### Results from our Pilots:
  In the `examples` folder we have the results from the following Pilots
  
## Pilots
In order to validate MedPerf we performed a series of pilot experiments with academic groups that are involved in multi-institutional collaborations for the purposes of research and development of medical AI models. The experiments were intentionally designed to include a diversity of domains and modalities in order to test MedPerf’s infrastructure adaptance. The experiments included public and private data highlighting the technical capabilities of MedPerf to operate on private data. We also asked participating teams to provide feedback on their experience with MedPerf (e.g., limitations, issues). 

**Data sources**

The figure below displays the data provider locations used in all pilot experiments. 🟢: Pilot 1 - Brain Tumor Segmentation Pilot Experiment; 🔴: Pilot 2 - Pancreas Segmentation Pilot Experiment. 🔵: Pilot 3 - Surgical Workflow Phase Recognition Pilot Experiment. Pilot 4 - Cloud Experiments, used data and processes from Pilot 1 and 2.

![image](https://user-images.githubusercontent.com/25375373/163238058-6cf16f00-5238-4c80-8b58-d86f291a5bcf.png)

### Pilot 1 - Brain Tumor Segmentation

**Participating institutions**

- University of Pennsylvania, Philadelphia, USA
- Perelman School of Medicine, Philadelphia, USA

**Task**

Gliomas are highly heterogeneous across their molecular, phenotypical, and radiological landscape. Their radiological appearance is described by different sub-regions comprising 1) the “enhancing tumor” (ET), 2) the gross tumor, also known as the “tumor core” (TC), and 3) the complete tumor extent also referred to as the “whole tumor” (WT). ET is described by areas that show hyper-intensity in T1Gd when compared to T1, but also when compared to ”healthy” white matter in T1Gd. The TC describes the bulk of the tumor, which is what is typically resected. The TC entails the ET, as well as the necrotic (fluid-filled) parts of the tumor. The appearance of the necrotic (NCR) tumor core is typically hypo-intense in T1Gd when compared to T1. The WT describes the complete extent of the disease, as it entails the TC and the peritumoral edematous/invaded tissue (ED), which is typically depicted by hyper-intense signal in T2-FLAIR.
These scans, with accompanying manually approved labels by expert neuroradiologists for these sub-regions, are provided in the International Brain Tumor Segmentation (BraTS) challenge data.

**Data**

The BraTS 2020 challenge dataset is a retrospective collection of 2,640 brain glioma multi-parametric magnetic resonance imaging (mpMRI) scans, from 660 patients, acquired at 23 geographically-distinct institutions under routine clinical conditions, i.e., with varying equipment and acquisition protocols.The exact mpMRI scans included in the BraTS challenge dataset are a) native (T1) and b) post-contrast T1-weighted (T1Gd), c) T2-weighted (T2), and d) T2-weighted Fluid Attenuated Inversion Recovery (T2-FLAIR). Notably, the BraTS 2020 dataset was utilized in the first ever federated learning challenge, namely the Federated Tumor Segmentation (FeTS) 2021 challenge (https://miccai.fets.ai/) that ran in conjunction with the Medical Image Computing and Computer Assisted Interventions (MICCAI) conference. Standardized pre-processing has been applied to all the BraTS mpMRI scans. This includes conversion of the DICOM files to the NIfTI file format, co-registration to the same anatomical template (SRI24), resampling to a uniform isotropic resolution (1mm3), and finally skull-stripping. The pre-processing pipeline is publicly available through the Cancer Imaging Phenomics Toolkit (CaPTk).

**Code**

[github.com/mlcommons/medperf/tree/main/examples/BraTS](https://github.com/mlcommons/medperf/tree/main/examples/BraTS)

### Pilot 2 - Pancreas Segmentation

**Participating institutions**

- Harvard School of Public Health, Boston, USA
- Dana-Farber Cancer Institute, Boston, USA

**Task**

Precise organ segmentation using computed tomography (CT) images is an important step for medical image analysis and treatment planning. Pancreas segmentation involves important challenges due to the small volume and irregular shapes of the areas of interest. Our goal is to perform federated evaluation across two different sites using MedPerf for the task of pancreas segmentation, to test the generalizability of a model trained on only one of these sites

**Data**

We utilized two separate datasets for the pilot experiment. The first of which is the Multi-Atlas Labeling Beyond the Cranial Vault (BTCV) dataset, which is publicly available through synapse platform. Abdominal CT images from 50 metastatic liver cancer patients and the postoperative ventral hernia patients were acquired at the Vanderbilt University Medical Center. The abdominal CT images were registered using NiftyReg.  In addition to the BTCV dataset, we also included another publicly available dataset from TCIA (The Cancer Imaging Archives) at the url (https://wiki.cancerimagingarchive.net/display/Public/Pancreas-CT); the National Institute of Health Clinical Center curated this dataset with 80 abdominal scans, from 53 male and 27 female subjects. Of which 17 patients had known kidney donations that confirmed healthy abdominal regions, and the remaining patients were selected after examination confirmed that the patients had neither pancreatic lesions nor any other significant abdominal abnormalities. Ourl visual inspection of both datasets confirmed that they were appropriate and complementary candidates for the pancreas segmentation task. Out of the 130 total cases, we used 10 subjects for inference, 5 from each dataset. We arbitrarily chose patients of IDs 1 to 5 from each one.

**Code**

[github.com/mlcommons/medperf/tree/main/examples/DFCI](https://github.com/mlcommons/medperf/tree/main/examples/DFCI)

### Pilot 3 - Surgical Workflow Phase Recognition

**Participating institutions**

- University Hospital of Strasbourg, France
- Policlinico Universitario Agostino Gemelli, Rome, Italy
- Azienda Ospedaliero-Universitaria Sant’Andrea, Rome, Italy
- Fondazione IRCCS Ca’ Granda Ospedale Maggiore Policlinico, Milan, Italy
- Monaldi Hospital, Naples, Italy

**Task**

Surgical phase recognition is a classification task of each video frame from a recorded surgery to one of some predefined phases that give a coarse description of the surgical workflow. This task is a building block for context-aware systems that help in assisting surgeons for better Operating Room (OR) safety.

**Data**

The data we used corresponds to Multichole2022; a multicentric dataset comprising videos of recorded laparoscopic cholecystectomy surgeries, annotated for the task of surgical phase recognition. The dataset consists of 180 videos in total, of which 56 videos were used in our pilot experiment and the rest of the videos (i.e., 124) were used to train the model. The videos were taken from five (5) different hospitals: 32 videos from the University Hospital of Strasbourg, France; which are part of the public dataset Cholec80, and 6 videos were taken from each of the following Italian hospitals: Policlinico Universitario Agostino Gemelli, Rome; Azienda Ospedaliero-Universitaria Sant’Andrea, Rome; Fondazione IRCCS Ca’ Granda Ospedale Maggiore Policlinico, Milan; and Monaldi Hospital, Naples. The data is still private for now. Videos are annotated according to the Multichole2022 annotation protocol, with 6 surgical phases: Preparation, Hepatocytic Triangle Dissection, Clipping and Cutting, Gallbladder Dissection, Gallbladder Packaging, and Cleaning / Coagulation

**Code**

[github.com/mlcommons/medperf/tree/main/examples/SurgMLCube](https://github.com/mlcommons/medperf/tree/main/examples/SurgMLCube)

### Pilot 4 - Cloud Experiments

**Task**

We proceeded to further validate MedPerf on the cloud. Towards this, we executed various parts of the MedPerf architecture across different cloud providers. Google Cloud Platform (GCP) was used across all experiments for hosting the server. The Brain Tumor Segmentation (BraTS) Benchmark (Pilot 1), as well as part of the Pancreas Segmentation Benchmark (Pilot 2), were executed inside a GCP Virtual Machine with 128GB of RAM and an Nvidia T4.
Lastly, we created a Chest X-Ray Pathology Classification Benchmark to demonstrate the feasibility of running federated evaluation across different cloud providers. For this, the CheXpert 40 small validation dataset was partitioned into 4 splits, and executed inside Virtual Machines provided by AWS, Alibaba, Azure, and IBM. All results were retrieved by the MedPerf server, hosted on GCP. The figure below shows which cloud provider each MedPerf component (i.e., server, client) and dataset was executed on.

**Data**

Here we used data and processes from Pilot #1 and #2.

**Code**

[github.com/mlcommons/medperf/tree/main/examples/Chest XRay](https://github.com/mlcommons/medperf/tree/main/examples/Chest%20XRay)

**Architecture**

![image](https://user-images.githubusercontent.com/25375373/163241596-464aa465-e517-41cd-b2c0-d698047c1ed2.png)

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
   We're going to be using the validation split. To ensure the data preparation step works properly, **please remove the `train.csv` from the `CheXpert-v1.0-small` folder.**
   
   ```
   rm ~/CheXpert-v1.0-small/train.csv
   ```
   The data preparation mlcube assumes that the input folder contains a single csv. Therefore, any other dataset that is used for this benchmark must follow that same assumption.
   
2. ## Authenticate the CLI
   If you followed the server hosting instructions, then your instance of the server already has some toy users to play with. The CLI needs to be authenticated with a user to be able to execute commands and interact with the server. For this, you can run:
   ```
   medperf login -u testdataowner -p test
   ```
   We just provided `testdataowner` as user and `test` as password. You only need to authenticate once. All following commands will be authenticated with that user.
3. ## Run the data preparation step
   Benchmarks will usually require a data owner to generate a new version of the dataset that has been preprocessed for a specific benchmark. The command to do that has the following structure
   ```
   medperf dataset create -b <BENCHMARK_UID> -d <PATH_TO_DATASET> -l <PATH_TO_LABELS> --name <DATASET NAME> --description <DESCRIPTION> --location <LOCATION>
   ```
   for the CheXpert dataset, this would be the command to execute:
   ```
   medperf dataset create -b 1 -d ~/CheXpert-v1.0-small -l ~/CheXpert-v1.0-small --name "Chexpert valid" --description "Chexpert valid" --location "Chexpert loc"
   ```
   Where we're executing the benchmark with UID `1`, since is the first and only benchmark in the server. By doing this, the CLI retrieves the data preparation cube from the benchmark and processes the raw dataset.
4. ## Run the benchmark execution step
   Once the dataset is prepared and registered, you can execute the benchmark with a given model mlcube. The command to do this has the following structure
   ```
   medperf run -b <BENCHMARK_UID> -d <DATA_UID> -m <MODEL_UID>
   ```
   For this demonstration, you would execute the following command:
   ```
   medperf run -b 1 -d 63a -m 2
   ```
   Given that the prepared dataset was assigned the UID of 63a. You can find out what UID your prepared dataset has with the following command:
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
- Instantiate and seed the server using `server/seed.py`
- Retrieve the demo dataset
- Run the CLI demo using `cli/cli.sh`
- cleanup temporary files

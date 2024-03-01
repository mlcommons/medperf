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
  
## Publications ##

If you use MedPerf, please cite our main paper: Karargyris, A., Umeton, R., Sheller, M.J. et al. Federated benchmarking of medical artificial intelligence with MedPerf. *Nature Machine Intelligence* **5**, 799–810 (2023). [https://www.nature.com/articles/s42256-023-00652-2](https://www.nature.com/articles/s42256-023-00652-2)

Additonally, here you can see how others used MedPerf already: [https://scholar.google.com/scholar?q="medperf"](https://scholar.google.com/scholar?q="medperf").

## Experiments

### FeTS Challenge ###

🎯 We pressure-tested MedPerf open benchmark framework by supporting the largest real-world federated study to date [FeTS - that was benchmarking 41 medical AI models across 32 treatment and research sites in 6 continents 🌎](https://miccai2022.fets.ai/) as well as on 🔓 public and 🔒 private data through medical research efforts across Dana-Farber Cancer Institute, Harvard T.H. Chan School of Public Health, University of Pennsylvania, Penn Medicine, University of Pennsylvania Health System, University of Strasbourg, Institute of Image-Guided Surgery (IHU Strasbourg), Fondazione Policlinico Universitario Agostino Gemelli IRCCS, and others with the pilot studies below. 

![image](https://github.com/mlcommons/medperf/assets/25375373/4b2876e8-d14a-4e24-b7dc-5a4508bfcaef)

## Pilot Studies ##

MedPerf was also further utilized to support academic medical research on both public and private data through efforts across Dana-Farber Cancer Institute, Harvard T.H. Chan School of Public Health, University of Pennsylvania, Penn Medicine, University of Pennsylvania Health System, University of Strasbourg, Institute of Image-Guided Surgery (IHU Strasbourg), Fondazione Policlinico Universitario Agostino Gemelli IRCCS, University of California San Francisco, and other academic institutions. The figure below displays the data provider locations used in all pilot experiments. 🟢: Pilot 1 - Brain Tumor Segmentation Pilot Experiment; 🔴: Pilot 2 - Pancreas Segmentation Pilot Experiment. 🔵: Pilot 3 - Surgical Workflow Phase Recognition Pilot Experiment. Pilot 4 - Cloud Experiments, used data and processes from Pilot 1 and 2.

![image](https://user-images.githubusercontent.com/25375373/163238058-6cf16f00-5238-4c80-8b58-d86f291a5bcf.png)

### POC 1 - Brain Tumor Segmentation

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

### POC 2 - Pancreas Segmentation

**Participating institutions**

- Harvard School of Public Health, Boston, USA
- Dana-Farber Cancer Institute, Boston, USA

**Task**

Precise organ segmentation using computed tomography (CT) images is an important step for medical image analysis and treatment planning. Pancreas Segmentation involves immense challenge due to the small volume and irregular shapes. Our goal is to perform federated evaluation across different sites using MedPerf for the task of pancreas segmentation.

**Data**

We utilized two separate datasets for the pilot experiment. The first of which is the Multi-Atlas Labeling Beyond the Cranial Vault (BTCV) dataset. This dataset is publicly available through synapse platform. Abdominal CT images from the metastatic liver cancer patients and the postoperative ventral hernia patients were acquired at the Vanderbilt University Medical Center. Voxel size for images was 0.6 to 0.9 mm in the anterior-posterior (AP) and left-right (LR) axis and 1.5 to 7.0 mm in the inferior-superior (IS) axis were the image acquisition parameters. Abdominal CT images were registered using NiftyReg. A total of 3719 images were obtained from 40 subjects for the task. 3719 images were randomly distributed into 2916 images for training, and 803 images for testing. The data distribution was done in a subject-wise manner to avoid data leakage between the training and the testing dataset. Due to the inconsistency in the image orientation, all the images were re-oriented to a standard orientation for further analysis.
In addition to the BTCV dataset, we also included another publicly available dataset from The Cancer Imaging Archives (TCIA). The National Institute of Health Clinical Center curated the dataset with 82 abdominal scans, from 53 male and 27 female subjects. Of which 17 patients had known kidney donations that confirmed healthy abdominal regions, and the remaining patients were selected after examination confirmed that the patients had neither pancreatic lesions nor any other significant abdominal abnormalities. These scans varied between 1.5 - 2.5 mm, with 512 x 512 pixel resolution, generating 18782 individual scans.

**Code**

[github.com/mlcommons/medperf/tree/main/examples/DFCI](https://github.com/mlcommons/medperf/tree/main/examples/DFCI)

### POC 3 - Surgical Workflow Phase Recognition

**Participating institutions**

- University Hospital of Strasbourg, France
- Policlinico Universitario Agostino Gemelli, Rome, Italy
- Azienda Ospedaliero-Universitaria Sant’Andrea, Rome, Italy
- Fondazione IRCCS Ca’ Granda Ospedale Maggiore Policlinico, Milan, Italy
- Monaldi Hospital, Naples, Italy

**Task**

Surgical phase recognition is a classification task of each video frame from a recorded surgery to one of some predefined phases that give a coarse description of the surgical workflow. This task is a building block for context-aware systems that help in assisting surgeons for better Operating Room (OR) safety.

**Data**

The data we used corresponds to [Multichole2022](https://arxiv.org/abs/2203.07345) a multicentric dataset generated by the research group [CAMMA](http://camma.u-strasbg.fr/) at IHU Strasbourg/University of Strasbourg comprising videos of recorded laparoscopic cholecystectomy surgeries, annotated for the task of surgical phase recognition. The dataset consists of 180 videos in total, of which 56 videos were used in our pilot experiment and the rest of the videos (i.e., 124) were used to train the model. The videos were taken from five (5) different hospitals: 32 videos from the University Hospital of Strasbourg, France; which are part of the public dataset Cholec80, and 6 videos were taken from each of the following Italian hospitals: Policlinico Universitario Agostino Gemelli, Rome; Azienda Ospedaliero-Universitaria Sant’Andrea, Rome; Fondazione IRCCS Ca’ Granda Ospedale Maggiore Policlinico, Milan; and Monaldi Hospital, Naples. The data is still private for now. Videos are annotated according to the Multichole2022 annotation protocol, with 6 surgical phases: Preparation, Hepatocytic Triangle Dissection, Clipping and Cutting, Gallbladder Dissection, Gallbladder Packaging, and Cleaning / Coagulation

**Code**

[github.com/mlcommons/medperf/tree/main/examples/SurgMLCube](https://github.com/mlcommons/medperf/tree/main/examples/SurgMLCube)

### POC 4 - Cloud Experiments

**Task**

We proceeded to further validate MedPerf on the cloud. Towards this, we executed various parts of the MedPerf architecture across different cloud providers. Google Cloud Platform (GCP) was used across all experiments for hosting the server. The Brain Tumor Segmentation (BraTS) Benchmark (Pilot 1), as well as part of the Pancreas Segmentation Benchmark (Pilot 2), were executed inside a GCP Virtual Machine with 128GB of RAM and an Nvidia T4.
Lastly, we created a Chest X-Ray Pathology Classification Benchmark to demonstrate the feasibility of running federated evaluation across different cloud providers. For this, the CheXpert 40 small validation dataset was partitioned into 4 splits, and executed inside Virtual Machines provided by AWS, Alibaba, Azure, and IBM. All results were retrieved by the MedPerf server, hosted on GCP. The figure below shows which cloud provider each MedPerf component (i.e., server, client) and dataset was executed on.

**Data**

Here we used data and processes from Pilot #1 and #2.

**Code**

[github.com/mlcommons/medperf/tree/main/examples/ChestXRay](https://github.com/mlcommons/medperf/tree/main/examples/ChestXRay)

**Architecture**

![image](https://user-images.githubusercontent.com/25375373/163241596-464aa465-e517-41cd-b2c0-d698047c1ed2.png)

## How to Use MedPerf
[Get Started](https://mlcommons.github.io/medperf/getting_started/overview/) with our hands-on tutorials.

## Documentation Contribution
If you wish to contribute to our documentation, here are the steps for successfully building and serving documentation locally:

- **Install dependencies:** We are currently using mkdocs for serving documentation. You can install all the requirements by running the following command:
  ```
  pip install -r docs/requirements.txt
  ``` 
- **Serve local documentation:** To run your own local server for visualizing documentation, run:
  ```
  mkdocs serve
  ```
- **Access local documentation:** Once mkdocs is done setting up the server, you should be able to access your local documentation website by heading to `http:/localhost:8000` on your browser.


# FeTS Challenge Guide for Evaluating Hospitals
This text describes all the steps required for evaluating hospitals to participate, prepare and execute the FeTS Challenge on their own datasets.

## FeTS Participation and Data Preparation
The following steps explain how to participate on the FeTS Challenge as an Evaluating Hospital.

### Get your MedPerf Account:
Currently, getting a new account requires contacting our admins. To get your account, email alejandro.aristizabal@factored.ai with the following information: 
1. Your desired username 
2. Your first name 
3. Your last name 
4. Your email address 
Alejandro will reply with the username and temporary password, which you can change once you have medperf installed. 

**NOTE:** In general, if you encounter any problems during the following steps, get in touch with Alejandro and Max (m.zenk@dkfz-heidelberg.de). We will do our best to find a solution quickly.

### Preliminary Set-up
To ensure a successful installation process, the following tools are needed/recommended: 
- **Git:** Required to retrieve the code. You can find installation instructions [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- **Anaconda/Miniconda:** Recommended for independent project environment. [Here](https://docs.anaconda.com/anaconda/install/linux/) are the installation instructions. Then, create a new environment with `conda create -y -n fets22_env pip` and activate it (`conda activate fets22_env`) before following the rest of the instructions.
- **Singularity:** Required, as it is the container engine that is going to be used throughout the benchmark. We recommend installing version 3.9.5, which is the same version used for testing. [Here](https://docs.sylabs.io/guides/3.9/user-guide/quick_start.html#quick-installation-steps) are the steps to install the specified version. Ensure you have the correct version by running:
	```
	singularity --version
	```
- **NVIDIA-GPU driver:** Please make sure your driver has version 450.51 or later. This is required to make sure that the singularity containers can use the GPU. One possible way to install the driver is described in [NVIDIA’s documentation](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#abstract).

### Get MedPerf
You can get the most up-to-date version of medperf by using the following command: 
```
git clone --branch fets-challenge https://github.com/mlcommons/medperf
cd medperf/cli
pip install -e .
```
Medperf requires Python 3.7 or above. The fets-challenge branch contains settings specific to the FeTS challenge. 

### Change MedPerf Password
Users are created by the MedPerf admin. If you haven’t received your credentials to access the server, get in touch with the team using the instructions above. 
Once you have your credentials, first log into medperf using the temporary password:
```
medperf login 
```
This command will prompt you to enter your username and password, and upon success, cache a local token. 
Next, change your password using the command: 
```
medperf passwd 
```
Once changed, log in a second time using the new password: 
```
medperf login
```
This refreshes your cached credentials. Under normal circumstances, you should not have to log in again for the duration of the challenge on the machine you are using. 

### Prepare your Dataset

The next step is to do final preparation, sanity-checking and MedPerf registration of your evaluation dataset. Note that none of your data will be uploaded. You will provide some descriptive information to help with organization that will be sent to the server (e.g. a name for the dataset), and will have the opportunity to review this small descriptor and cancel the upload if you wish (this would prevent evaluation).

#### Dataset Preparation
First, we “create” a new dataset entry, using the preparation logic required by the benchmark. We will need to pass a number of details on the command line. You’ll need: 
1. <path/to/data>, which is the path to the directory where your dataset resides. Later, you’ll need to pass it to the command twice: once for where the data is and once for where the labels are. We follow the file structure from the FeTS initiative, so these should be the same directory, which should look like:
  ```
  path/to/data/
  │  
  └───Patient_001 # case identifier
  │   │ Patient_001_brain_t1.nii.gz  # also accepted without _brain (same for other modalities)
  │   │ Patient_001_brain_t1ce.nii.gz
  │   │ Patient_001_brain_t2.nii.gz
  │   │ Patient_001_brain_flair.nii.gz
  │   │ Patient_001_final_seg.nii.gz
  │   
  └───Pat_JohnDoe # other case identifier
  │   │ ...
  ```
2. `<path/to/data>`, which is the file path to where your dataset resides. You’ll need to type it twice: once for where the data is and once for where the labels are. Given the typical brats file structure, these should be the same directory. 
3. `<name>`, which is whatever name you would like the dataset to show in medperf, e.g. `"ACME FeTS 2022"`. (Quotes are required if using spaces) 
4. `<description>` which is information that can be helpful for benchmark committees to find datasets of interest. 
5. `<location>` which gives some information about where the data comes from. Useful when analyzing geographic diversity.
**NOTE:** The `<name>` `<description>` and `<location>` fields have a hard limit of 20 characters. Beyond this, you will get an error from the server.

```
medperf --log=debug dataset create -b 5 -d <path/to/data> -l <path/to/data> --name |<name>" --description "<description>" --location "<location>"
```
This command will execute the Data Preparation MLCube provided by the specified benchmark. It will result in a new version of the original dataset, which has been transformed, checked and analyzed for model execution. 
Information about the dataset (like its UID) can be obtained with: 
```
medperf dataset ls
```
For example, the above command might print the following to the terminal
```
MedPerf 0.0.0
UID                                           Server UID  Name           Data Preparation Cube UID  Registered    Local
—---------------------------------------   ---—---------  —------------  —------------------------  —---------    —-----
d0f29312da6652dd33296282c25a1da58426ba98               1  ACME FeTS2022                          1       False.     True
```

Note the `UID` value. That’s a unique identifier for your dataset that you’ll need for the next command. You’ll only need the first few characters. In the above case, I was able to pass “d0f” to the system and it could determine the right dataset. 

**NOTE:** At this point, we need you to **send a small piece of information to us via email**, which can currently not be collected through MedPerf: Please check the output of the command
```
wc -l <path/to/data>/split_info/fets_phase2_split_1/val.csv
```
where you have to insert the path to your data as before, and send it to us. This prints the number of lines in the file if it exists or an error message if it does not exist (which may happen and is not a problem).

#### Dataset Submission
Once a prepared dataset has been created, it can be submitted to the medperf platform. As mentioned above, for the <dataset_uid> parameter, you only need the first few characters of the dataset ID (just enough to ensure the system can distinguish the value from others). 
```
medperf dataset submit -d <dataset_uid> 
```
**NOTE:** submitting a dataset is not the same as uploading the dataset. The data stays in the user’s machine, and only metadata regarding the dataset is uploaded, which must be approved beforehand by the user. 

This command will show you the exact registration information that will be sent to the server and ask you to approve the submission. For example, in the toy example above, the output was:

```
MedPerf 0.0.0

====================
data_preparation_mlcube: '1'
description: BraTS compat MRIs
generated_uid: d0f29312da6652dd33296282c25a1da58426ba98
input_data_hash: cc1c0dc5545e636da71fdae4211259a8a0f0
location: Cornelius
metadata:
  Invalid_Subjects: 0
  Valid_Subjects: 5
name: ACME FeTS2022
separate_labels: true
split_seed: 0
state: OPERATION
status: PENDING

====================
Above is the information and statistics that will be registered to the database
Do you approve the registration of the peresented data to the MLCommons comms? [Y/n] Y
```

If you approve, enter `y` and the registration will upload exactly the information shown (it will be tied to your user id in the MedPerf system as well). 

#### Dataset Association
The last step is to “associate” this dataset with the benchmark. This will send a request to the benchmark owner to participate as a data owner in that benchmark. As part of this process, it will run the benchmark’s reference model to ensure compatibility with the benchmark. This process will download the reference model, metrics logic, and then run the reference pipeline against your dataset. **This could take anywhere from 10 minutes to a few hours depending on the size of your dataset.**
```
medperf --log=debug dataset associate -d <dataset_uid> -b 5 
```

If this process succeeds, you are all done with data preparation! The benchmark owner (Max from DKFZ) will see your association request and approve it. After that, you will be able to run any model that is added to the benchmark. 

## FeTS Challenge Evaluation
This folder contains scripts for the execution and submission of results related to the FeTS Challenge. 

### Prerequisites
It is expected that the user already has a prepared dataset, which has been submitted to the platform, associated with the FeTS Benchmark and approved by the FeTS organizers.
   This can be confirmed with the following command
   ```
   medperf association ls
   ```
   which should display an association with status `APPROVED`

### Contents
For evaluating challenge submissions, we provide the following files: 
- `run_models.py`: script for automatically executing all models for a specific benchmark.
- `submit_results.py`: script for automatically submitting all results for a specific benchmark.
- `fets_subm_list.json`: file containing models names for the FeTS Challenge.
- `brats_evaluation_priority.json` file containing models names for the BraTS Model Evaluation.
As you cloned the Medperf repository earlier during data preparation, you can find them in the `scripts` folder (relative to your local Medperf repository).
Here is a brief description of all the files contained in this folder:

### How to Use
To properly run the scripts provided, you need to know the following information:
- **The benchmark UID:** The currently accepted benchmark uid is `5`
- **The Dataset UID:** You can find your dataset UID by running
  ```
  medperf dataset ls
  ```
  If you have more than one dataset, you can find out which ones are associated to the specified benchmark by taking note of the dataset `Server UID` (found from the previous command) and looking at what benchmark is associated with, using the following command:
  ```
  medperf association ls
  ```
- **The number of subjects in the data:** This can be determined by looking at the registration information related to your dataset. You can find that by running the following command
  ```
  cat ~/.medperf_fets/data/<DATASET_UID>/registration-info.yaml
  ```
  inside there you will see the `Valid_Subjects` key, which specifies the number of cases that will be processed.
  
Once you have gathered above information, you can continue to run model inference on your data by following the instructions below. You may notice that they contain two calls to the evaluation script. This is because we have two sets of model submissions this year: *FeTS submissions*, which are new models submitted to this year’s challenge and *BraTS submissions*, which are models from BraTS 2021 adapted for the FeTS challenge. As it is more urgent to get results for the FeTS submissions, we evaluate them first.

### Evaluate FeTS Submissions:
#### 1. Models execution:
   To generate results for the FeTS Challenge, you need to execute the following command
   ```
   python run_models.py -b <BENCHMARK_UID> -d <DATASET_UID> -n <NUM_SUBJECTS> --no-test --no-cleanup -t 300
   ```
   This will initiate the model execution process, and go through all the models specified in the helper file (by default `fets_subm_list.json`). Evaluation will take from a few hours to one day.

   **NOTE:** This command will download singularity image files for each model, which will take up 30GB of storage. If you don’t have enough disk space, you can omit the `--no-cleanup` option, so that image files are deleted after a model has been evaluated.
   
   If any model fails, it will say so in the stdout, and continue running the rest of the models. The script will only execute models which have not yet generated any results, which means that it can be executed multiple times to retry models which may have failed in the past.
#### 2. Results Submission:
   To submit the generated results, we offer two options:
   - Skip approval step: Faster, and requires no further input from the user. **This is only recommended if the collaborator trusts the results will not leak any private information.**
     ```
     python submit_results.py -b <BENCHMARK_UID> -y
     ```
   - Manual approval: The collaborator can see the generated results for each model, and manually approves result submission.   
	 ```
	 python submit_results.py -b <BENCHMARK_UID>
	 ```
   
   This command can be cancelled and resumed at any time. It will ask for submission confirmation for any results that have not been submitted already, which means that approved results will be ommited on a second run, but pending/not approved ones will be displayed again for submission confirmation.

### Evaluate BraTS Submissions
For the BraTS Evaluation process, the previous steps will be executed again but using the `brats_evaluation_priority.json`
#### 1. Models execution:
Use the following command to execute the BraTS models. Evaluation will take from a few days to one week.
```
python run_models.py -b <BENCHMARK_UID> -d <DATASET_UID> -n <NUM_SUBJECTS> -m brats_evaluation_priority.json
```

**NOTE:** This command will automatically remove each model after successful execution. This is in order to save storage space, as the total space used by all the BraTS models is around 157GB. If you wish to keep the models for either re-execution with multiple datasets, or debugging, then please provide the `--no-cleanup` option to the above command.

#### 2. Results Submission:
If there's no need to manually approve each result, use the following command
```
python submit_results.py -b <BENCHMARK_UID> -y
```
**This is only recommended if the collaborator trusts the results will not leak any private information.**
Else, use this one for manually approving each submission 
```
python submit_results.py -b <BENCHMARK_UID>
```

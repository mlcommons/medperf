# FeTS-related Scripts
This folder contains scripts for the execution and submission of results related to the FeTS Challenge. 

## Prerequisites
1. It is expected that the user already has a prepared dataset, which has been submitted to the platform, associated with the FeTS Benchmark and approved by the FeTS organizers.
   This can be confirmed with the following command
   ```
   medperf association ls
   ```
   which should display an association with status `APPROVED`
2. Singularity 3.9.5
3. CUDA >= 450

## Contents
Here is a brief description of all the files contained in this folder:
- `run_models.py`: script for automatically executing all models for a specific benchmark.
- `submit_results.py`: script for automatically submitting all results for a specific benchmark.
- `fets_subm_list.json`: file containing models names for the FeTS Challenge.
- `brats_evaluation_priority.json` file containing models names for the BraTS Model Evaluation.
## How to Use
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
### FeTS Evaluation and submission:
#### 1. Models execution:
   To generate results for the FeTS Challenge, you need to execute the following command
   ```
   python run_models.py -b <BENCHMARK_UID> -d <DATASET_UID> -n <NUM_SUBJECTS> -t 258
   ```
   This will initiate the model execution process, and go through all the models specified in the helper file (by default `fets_subm_list.json`) with an expected execution time of 4.3 minutes per case per model. 
   
   If any model fails, it will say so in the stdout, and continue running the rest of the models. The script will only execute models which have not yet generated any results, which means that it can be executed multiple times to rety models which may have failed in the past.
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

### BraTS Evaluation and Submission
For the BraTS Evaluation process, the previous steps will be executed again but using the `brats_evaluation_priority.json`
#### 1. Models execution:
Use the following command to execute the BraTS models with an expected execution time of 47 minutes per case per model.
```
python run_models.py -b <BENCHMARK_UID> -d <DATASET_UID> -n <NUM_SUBJECTS> -t 2820 -m brats_evaluation_priority.json
```

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
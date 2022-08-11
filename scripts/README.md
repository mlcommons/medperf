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

## How to Use
1. **Models execution:**
   To generate results, the script `run_models` has been provided. It uses a helper file (by default `brats_evaluation_priority.json`) to determine the models to be executed and their order of priority. To execute with the current benchmark, you need to know the following information:
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

   Once all of this information is gathered, you can execute the benchmark with the following command
   ```
   python run_models.py -b <BENCHMARK_UID> -d <DATASET_UID> -n <NUM_SUBJECTS>
   ```
   This will initiate the model execution process, and go through all the models specified in the helper file. If any model fails, it will say so in the stdout, and continue running the rest of the models. The script will only execute models which have not yet generated any results, which means the script can be executed multiple times to rety models which may have failed in the past.
2. **Results Submission:**
   Once results for all models have been generated, it is necessary to submit results to the medperf server. For this, the `submit_results.py` script has been provided. It submits all of the results, while allowing the collaborator to look and confirm the desire to upload each result individually. To execute, you only need to know:
   - **The benchmark UID:** The currently accepted benchmark uid is `5`
   With that, you can initiate the submission step by running the following command:
   ```
   python submit_results.py -b <BENCHMARK_UID>
   ```
   It will ask for input from the collaborator for each and every result before sending them to the server. Optionally, the `-y` option has been provided, which skips the approval step by auto-approving all of the results. **This is only recommended if the collaborator trusts the results will not leak any private information**.

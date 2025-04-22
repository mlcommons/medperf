<!-- # MedPerf Benchmarking Workflow

![](./images/full_diagram.PNG) -->

<!-- ## Creating a User

Currently, the MedPerf administration is the only one able to create users, controlling access to the system and permissions to own a benchmark. For example, if a hospital (Data Owner), a model owner, or a benchmark committee wants to have access to MedPerf, they need to contact the MedPerf administrator to add a user. -->


<style>
td, th {
   border: none!important;
}
</style>


A benchmark in MedPerf is a collection of assets that are developed by the benchmark committee that aims to evaluate medical ML on decentralized data owners.

The process is simple yet effective enabling scalability.

## Step 1. Establish Benchmark Committee

The benchmarking process starts with establishing a benchmark committee of healthcare stakeholders (experts, committee), which will identify a clinical problem where an effective ML-based solution can have a significant clinical impact.

<!-- ## Step 2. Recruit Data and Model Owners

The benchmark committee recruits Data Owners and Model Owners either by inviting trusted parties or by making an open call for participation. A higher number of dataset providers recruited can maximize diversity on a global scale. -->

## Step 2. Register Benchmark

[MLCubes](mlcubes/mlcubes.md) are the building blocks of an experiment and are required in order to create a benchmark. Three MLCubes (Data Preparator MLCube, Reference Model MLCube, and Metrics MLCube) need to be submitted. After submitting the three MLCubes, alongside with a sample reference dataset, the Benchmark Committee is capable of creating a benchmark. Once the benchmark is submitted, the Medperf admin must approve it before it can be seen by other users. Follow our [Hands-on Tutorial](getting_started/benchmark_owner_demo.md) for detailed step-by-step guidelines.

## Step 3. Register Dataset

Data Owners that want to be part of the benchmark can [register their own datasets, prepare them, and associate them](getting_started/data_owner_demo.md) with the benchmark. A dataset will be prepared using the benchmark's Data Preparator MLCube and the dataset's **metadata** is registered within the MedPerf server.

| ![flow_preparation.gif](images/flow_preparation_association_folders.PNG) | 
|:--:| 
| *Data Preparation* |


The data owner then can request to participate in the benchmark with their dataset. Requesting the association will run the benchmark's reference workflow to assure the compatibility of the prepared dataset structure with the workflow. Once the association request is approved by the Benchmark Committee, then the dataset becomes a part of the benchmark.

![](./images/dataset_preparation_association.png)

## Step 4. Register Models

Once a benchmark is submitted by the Benchmark Committee, any user can [submit their own Model MLCubes](getting_started/model_owner_demo.md) and [request an association with the benchmark](getting_started/model_owner_demo.md#3-request-participation). This association request executes the benchmark locally with the given model on the benchmark's reference dataset to ensure workflow validity and compatibility. If the model successfully passes the compatibility test, and its association is approved by the Benchmark Committee, it becomes a part of the benchmark.

![](./images/submitting_associating_additional_models_1.png)

## Step 5. Execute Benchmark

The Benchmark Committee may notify Data Owners that models are available for benchmarking. Data Owners can then [run the benchmark models](getting_started/data_owner_demo.md#5-execute-the-benchmark) locally on their data.

This procedure retrieves the model MLCubes associated with the benchmark and runs them on the indicated prepared dataset to generate predictions. The Metrics MLCube of the benchmark is then retrieved to evaluate the predictions. Once the evaluation results are generated, the data owner can [submit them](getting_started/data_owner_demo.md#6-submit-a-result) to the platform.

![](./images/execution_flow_folders.PNG)

## Step 6. Aggregate and Release Results

The benchmarking platform aggregates the results of running the models against the datasets and shares them **according to the Benchmark Committee's policy.**

The sharing policy controls how much of the data is shared, ranging from a single aggregated metric to a more detailed model-data cross product. A public leaderboard is available to Model Owners who produce the best performances.

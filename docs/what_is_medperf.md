
<style>
td, th {
   border: none!important;
}
</style>
MedPerf is an open-source framework for benchmarking medical ML models. It uses *Federated Evaluation* a method in which medical ML models are securely distributed to multiple global facilities for evaluation prioritizing patient privacy to mitigate legal and regulatory risks. The goal of *Federated Evaluation* is to make it simple and reliable to share ML models with many data owners, evaluate those ML models against their data in controlled settings, then aggregate and analyze the findings. 

The MedPerf approach empowers healthcare stakeholders through neutral governance to assess and verify the performance of ML models in an efficient and human-supervised process without sharing any patient data across facilities during the process.



| ![federated_evaluation.gif](images/fed_eva_example.gif) | 
|:--:| 
| *Federated evaluation of medical AI model using MedPerf on a hypothetical example* |


## Why MedPerf?

MedPerf aims to identify bias and generalizability issues of medical ML models by evaluating them on diverse medical data across the world. This process allows developers of medical ML to efficiently identify performance and reliability issues on their models while healthcare stakeholders (e.g., hospitals, practices, etc.) can validate such models against clinical efficacy.

Importantly, MedPerf supports technology for **neutral governance** in order to enable **full trust** and **transparency** among participating parties (e.g., AI vendor, data owner, regulatory body, etc.). This is all encapsulated in the benchmark committee which is the overseeing body on a benchmark.

| ![benchmark_committee.gif](images/benchmark_committee.gif) | 
|:--:| 
| *Benchmark committee in MedPerf* |

## Benefits to healthcare stakeholders

Anyone who joins our platform can get several benefits, regardless of the role they will assume.

| ![benefits.png](images/benefits.png) | 
|:--:| 
| *Benefits to healthacare stakeholders using MedPerf* |

[Our paper](https://www.nature.com/articles/s42256-023-00652-2){target="_blank"} describes the design philosophy in detail.

<!-- ## What is a benchmark in the MedPerf perspective?

A benchmark is a collection of assets used by the platform to test the performance of ML models for a specific clinical problem. The primary components of a benchmark are:

1. **Specifications**: precise definition of the clinical setting (e.g., problem or task and specific patient population) on which trained ML models are to be evaluated. It also includes the labeling (annotation) methodology as well as the choice of evaluation metrics.
2. **Dataset Preparation**: a process that prepares datasets for use in evaluation, and can also test the prepared datasets for quality and compatibility. This is implemented as an MLCube (see [Data Preparator MLCube](mlcubes/mlcubes.md#data-preparator-mlcube)).
3. **Registered Datasets**: a list of registered datasets prepared according to the benchmark criteria and approved for evaluation use by their owners (e.g. patient data from multiple facilities representing (as a whole) a diverse patient population).
4. **Evaluation**: a consistent implementation of the testing pipelines and evaluation metrics.
5. **Reference Implementation**: a detailed example of a benchmark submission consisting of example model code, the evaluation component, and de-identified or synthetic publicly available sample data.
6. **Registered Models**: a list of registered models to run in this benchmark.
7. **Documentation**: documents for understanding and using the benchmark. -->

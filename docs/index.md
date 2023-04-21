# Introduction

Medical Artificial Intelligence (AI) has the potential to revolutionize healthcare by advancing evidence-based medicine, personalizing patient care, and reducing costs. Unlocking this potential requires reliable methods for evaluating the efficacy of medical machine learning (ML) models on large-scale heterogeneous data while maintaining patient privacy.

## What is MedPerf?

MedPerf is an open-source framework for benchmarking ML models to deliver clinical efficacy while prioritizing patient privacy and mitigating legal and regulatory risks. It enables federated evaluation in which models are securely distributed to different facilities for evaluation. The goal of federated evaluation is to make it simple and reliable to share models with many data providers, evaluate those models against their data in controlled settings, then aggregate and analyze the findings.

The MedPerf approach empowers healthcare organizations to assess and verify the performance of ML models in an efficient and human-supervised process without sharing any patient data across facilities during the process.

## Why MedPerf?

MedPerf reduces the risks and costs associated with data sharing, maximizing medical and patient outcomes. The platform leads to an effective, broader, and cost-effective adoption of medical ML and improves patient outcomes.

Anyone who joins our platform can get several benefits, regardless of the role they will assume.

**Benefits if you are a [Data Provider](roles.md#data-providers):**

* Evaluate how well machine learning models perform on your population’s data.
* Connect to Model Owners to help them improve medical ML in a specific domain.
* Help define impactful medical ML benchmarks.

**Benefits if you are a [Model Owner](roles.md#model-owners):**

* Measure model performance on private datasets that you would never have access to.
* Connect to specific Data Providers that can help you increase the performance of your model.

**Benefits if you own a benchmark ([Benchmark Committee](roles.md#benchmark-committee)):**

* Hold a leading role in the MedPerf ecosystem by defining specifications of a benchmark for a particular medical ML task.
* Get help to create a strong community around a specific area.
* Rule point on creating the guidelines to generate impactful ML for a specific area.
* Help improve best practices in your area of interest.
* Ensure the choice of the metrics as well as the proper reference implementations.

**Benefits to the Broad Community:**

* Provide consistent and rigorous approaches for evaluating the accuracy of ML models for real-world use in a standardized manner.
* Enable model usability measurement across institutions while maintaining data privacy and model reliability.
* Connect with a community of expert groups to employ scientific evaluation methodologies and technical approaches to operate benchmarks that not only have well-defined clinical aspects, such as clinical impact, clinical workflow integration and patient outcome, but also support robust technical aspects, including proper metrics, data preprocessing and reference implementation.

## What is a benchmark in the MedPerf perspective?

A benchmark is a collection of assets used by the platform to test the performance of ML models for a specific clinical problem. The primary components of a benchmark are:

1. **Specifications**: precise definition of the clinical setting (e.g., problem or task and specific patient population) on which trained ML models are to be evaluated. It also includes the labeling (annotation) methodology as well as the choice of evaluation metrics.
2. **Dataset Preparation**: a process that prepares datasets for use in evaluation, and can also test the prepared datasets for quality and compatibility. This is implemented as an MLCube (see [Data Preparator MLCube](mlcubes/mlcubes.md#data-preparator-mlcube)).
3. **Registered Datasets**: a list of registered datasets prepared according to the benchmark criteria and approved for evaluation use by their owners (e.g. patient data from multiple facilities representing (as a whole) a diverse patient population).
4. **Evaluation**: a consistent implementation of the testing pipelines and evaluation metrics.
5. **Reference Implementation**: a detailed example of a benchmark submission consisting of example model code, the evaluation component, and de-identified or synthetic publicly available sample data.
6. **Registered Models**: a list of registered models to run in this benchmark.
7. **Documentation**: documents for understanding and using the benchmark.

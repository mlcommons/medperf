In this tutorial we will create a benchmark that classifies chest X-Ray images.

### Demo Data

The `medperf_tutorial/demo_data/` folder contains the demo dataset content.
  
  - `images/` folder includes sample images.
  - `labels/labels.csv` provides a basic ground truth markup, indicating the class each image belongs to.

You should share your demo dataset publicly with all benchmark users for two key purposes:
  1. External Data Owners can understand the exact format required for their data to participate in the benchmark.
  2. External Model Owners can test their models using this sample. After implementing their model as an MLCube, they can conduct tests without needing access to real data (hosted by Data Owners). Note: Model MLCubes do not consume raw data but rather prepared data; see [DataPreparator MLCube folder](#data-preparator-mlcube).
  
  To reiterate: The purpose of the demo dataset in every benchmark is to demonstrate users the __expected data format__ your benchmark requires, not to distribute real data.

### Data Preparator MLCube

The `medperf_tutorial/data_preparator/` contains a [DataPreparator MLCube](../../../mlcubes/mlcube_data.md) that you must implement. This MLCube:
  - Transforms [raw demo data](#demo-data) into a format convenient for model consumption, such as converting DICOM images into numpy tensors, cropping patches, normalizing columns, etc. It's up to you to define the format that is handy for future models.
  - Ensures its output is in a standardized format, allowing Model Owners/Developers to rely on its consistency.
  - Requires that real Dataset Owners joining your benchmark later prepare their data in a form compatible with your Data Preparator.

### Model MLCube

The `medperf_tutorial/model_custom_cnn/` is an example of a [Model MLCube](../../../mlcubes/mlcube_models.md). You need to implement a basic mock-up model for users to verify the entire pipeline is working. Model Developers joining your benchmark will replace this MLCube with their own implementations.

### Metrics MLCube

The `medperf_tutorial/metrics/` houses a [Metrics MLCube](../../../mlcubes/mlcube_metrics.md) that processes ground truth data, model predictions, and computes basic statistics - such as classification accuracy, loss, etc. After a Dataset Owner runs models on their data, these final metric values will be shared with you as the Benchmark Owner. Please ensure that your metrics are not too specific and do not reveal any Personally Identifiable Information (PII) or other confidential data (including dataset statistics) - otherwise, no Dataset Owners would agree to participate in your benchmark!

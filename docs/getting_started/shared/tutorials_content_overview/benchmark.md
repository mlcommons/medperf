In this tutorial we will create a benchmark that classifies chest X-Ray images.

### Demo Data

The `medperf_tutorial/demo_data/` folder contains the demo dataset content.
  
  - `images/` folder includes sample images.
  - `labels/labels.csv` provides a basic ground truth markup, indicating the class each image belongs to.

The demo dataset is a sample dataset used for the development of your benchmark and used by Model Owners for the development of their models. More details are available in the [section below](#2-develop-a-demo-dataset)

### Data Preparator Container

The `medperf_tutorial/data_preparator/` contains a [DataPreparator container](../../../containers/containers.md#data-preparator-container) that you must implement. This container:

  - Transforms raw data into a format convenient for model consumption, such as converting DICOM images into numpy tensors, cropping patches, normalizing columns, etc. It's up to you to define the format that is handy for future models.
  - Ensures its output is in a standardized format, allowing Model Owners/Developers to rely on its consistency.

### Model Container

The `medperf_tutorial/model_custom_cnn/` is an example of a [Model Container](../../../containers/containers#model-container.md). You need to implement a reference model which will be used by data owners to test the compatibility of their data with your pipeline. Also, Model Developers joining your benchmark will follow the input/output specifications of this model when building their own models.

### Metrics Container

The `medperf_tutorial/metrics/` houses a [Metrics Container](../../../containers/containers.md#metricsevaluator-container) that processes ground truth data, model predictions, and computes performance metrics - such as classification accuracy, loss, etc. After a Dataset Owner runs the benchmark pipeline on their data, these final metric values will be shared with you as the Benchmark Owner.

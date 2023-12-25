### Demo data

`medperf_tutorial/demo_data/` folder contains demo dataset content.
  - `images/` folder contains sample images
  - `labels/labels.csv` contains a simple ground truth markup: which image belongs to which class

  The demo dataset would be publicly shared among all benchmark users. It's required for two purposes:
  1. External Data Owners can see what exactly format their data should be transformed to in order to be attached to participate in benchmark.
  2. External Model Owners can check their models on this sample. After model owner implements their model MLCube, they can test it without access to a real data (hosted by Data Owners). NB: Model MLCubes consume not the raw data but prepared one; see [DataPreparator MLCube folder](#data-preparator-mlcube).
  
  So, once more: demo dataset is necessary to show __expected data format__ that your benchmark consumes, not to share a real data.

### Data Preparator MLCube

`medperf_tutorial/data_preparator/` is a [DataPreparator MLCube](../../../mlcubes/mlcube_data.md) that you have to implement. This MLCube 
  - Converts [raw demo data](#demo-data) to some convenient form, usable to be consumed by models: converts DICOM images to numpy tensors, or crop patches, or normalize columns, or... It's up to you to decide which format is handy for future models.
  - Guarantees its output has the fixed format, so Model Owners / Model Developers can rely on that.
  - The real Dataset Owners that will join your benchmark later would ought to prepare their data in the form your Data Preparator can consume it.

### Model MLCube

`medperf_tutorial/model_custom_cnn/` is an example of [Model MLCube](../../../mlcubes/mlcube_models.md). Your need to implement a simple mockup model to ensure the whole pipeline is working. Model developers who would join your benchmark would replace this MLCube with their own implementation.

### Metrics MLCube

`medperf_tutorial/metrics/` is a [Metrics MLCube](../../../mlcubes/mlcube_metrics.md) that consumes ground truth, model predictions and evaluates some basic stats - classification accuracy, loss,  etc. After Dataset Owner runs models over his data, these final metrics values would be shared to you as Benchmark Owner. Please, ensure your metrics are not too specific and do not leak any PII or other confidential information (including dataset statistics) - in other case no Dataset Owners would agree to participate in your benchmark!

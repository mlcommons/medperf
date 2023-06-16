# BraTS MLCubes

**(This example is currently not compatible with the latest MedPerf version. This will be fixed soon)**

This contains examples to create MLCubes for the [Brain Tumor Segmentation (BraTS) challenge](http://braintumorsegmentation.org/).

This Folder contains 5 MLCubes:

### data_prep

A data preparation MLCube of brain tumor MR scans that have ground truth annotations. For more information, see "Data" under http://braintumorsegmentation.org/.

### model_deepmedic

A model MLCube for running inference on prepared brain tumor MR scans using [DeepMedic](https://doi.org/10.1016/j.media.2016.10.004) trained on BraTS 2020 training data.

### model_deepscan

A model MLCube for running inference on prepared brain tumor MR scans using [DeepScan](https://doi.org/10.1007/978-3-030-11726-9_40) trained on BraTS 2020 training data - this requires 120G RAM.

### model_nnunet

A model MLCube for running inference on prepared brain tumor MR scans using [nnUNet](https://doi.org/10.1038/s41592-020-01008-z) trained on BraTS 2020 training data.

### metrics

The official BraTS metrics calculation MLCube using predictions from models and ground truth using the [Cancer Imaging Phenomics Toolkit (CaPTk)](https://cbica.github.io/CaPTk/BraTS_Metrics.html).

### Tutorial's Dataset Example

The `medperf_tutorial/sample_raw_data/` folder contains your data for the specified Benchmark. In this tutorial, where the benchmark involves classifying chest X-Ray images, your data comprises:

- `images/` folder contains your images
- `labels/labels.csv`, which provides the ground truth markup, specifying the class of each image.

The format of this data is dictated by the Benchmark Owner, as it must be compatible with the benchmark's Data Preparation MLCube. In a real-world scenario, the expected data format would differ from this toy example. Refer to the Benchmark Owner to get a format specifications and details for your practical case.

As previously mentioned, your data itself never leaves your machine. During the dataset submission / sharing, only basic metadata is transferred.


# Instructions for Model Owners 

## Implementing the Model MLCube

Model Owners that want to submit and associate models to a benchmark need to implement a new Model MLCube following the structure and conventions MedPerf uses to successfully run models on the platform. You can get details on how to implement the Model MLCube [here](https://github.com/aristizabal95/mlcube_examples/tree/medperf-examples/medperf/model).  

## Testing Your MLCube

After developing your MLCube, you can test if your implementation follows the expected I/O of the benchmark. For such, use the following command:

```
medperf test -b <benchmark_uid> -m <path/to/model/mlcube>
```

Then CLI will provide a response as follows:

```
MedPerf 0.0.0
Benchmark Data Preparation: tmp_1_test_1655394059_3
> Preparation cube download complete
> MLCommons TorchXRayVision Preprocessor MD5 hash check complete
> Cube execution complete
> Sanity checks complete
> Statistics complete
Benchmark Execution: tmp_1_test_1655394059_3
> Metrics cube download complete
> MLCommons Metrics MD5 hash check complete
> Model cube download complete
> MLCommons TorchXRayVision CheXpert DenseNet model MD5 hash check complete
> Model execution complete
✅ Done!
```

## Submitting Your MLCube

To submit your MLCube, you should have the following information at hand:

* <strong><code>mlcube.yaml</code></strong> raw github url with commit hash
* <strong><code>parameters.yaml</code></strong> raw github url with commit hash
* URL for the additional files tarball (optional)

You can submit your MLCube using the following command:

```
medperf mlcube submit --name <mlcube_name> --mlcube-file 
```

Then CLI will return a response as follows:

```
https://raw.githubusercontent.com/aristizabal95/medical/02e142f9a83250a0108e73f955bf4cb6c72f5a0f/cubes/xrv_chex_densenet/mlcube/mlcube.yaml --parameters-file https://raw.githubusercontent.com/aristizabal95/medperf-server/1a0a8c21f92c3d9a162ce5e61732eed2d0eb95cc/app/database/cubes/xrv_chex_densenet/parameters.yaml --additional-file https://storage.googleapis.com/medperf-storage/xrv_chex_densenet.tar.gz --additional-hash c5c408b5f9ef8b1da748e3b1f2d58b8b3eebf96e
MedPerf 0.0.0
Additional file hash generated
✅ Done!
```

**Note:** Currently, it is not possible to edit your submission, so ensure the information is correct. This will change in the near future, and instructions might need to be updated.

### Getting information about your MLCubes 

You can get information on your submitted MLCubes through:

```
medperf mlcube ls
```

Then CLI will provide a response as follows:

```
MedPerf 0.0.0
  MLCube UID  Name       State
------------  ---------  ---------
           5  densenet2  OPERATION
```

## Requesting Association to a Benchmark

Once that cube passes the test and is submitted to the platform, you can create an association to the desired benchmark with:

```
medperf mlcube associate -m <mlcube_uid> -b <benchmark_uid>
```

The CLI will return a simple response to confirm the association request:

```
MedPerf 0.0.0
✅ Done!
```

Once an association is created, the Benchmark Committee must approve it. If the association is for a benchmark that you own, then it will be automatically approved and you can start using the model with your benchmark.

### Retrieving an association 

Existing associations can be retrieved with the following command:

```
medperf association ls
```

And the CLI will provide a list of associations:

```
MedPerf 0.0.0
Dataset UID      MLCube UID    Benchmark UID    Initiated by  Status
-------------  ------------  ---------------  --------------  --------
                         32                7              13  APPROVED
                         33                7              13  APPROVED
                         35                7              13  APPROVED
                         38                7              13  APPROVED
                         37                7              13  PENDING
```

(WIP)

To define and submit a benchmark, the benchmark owner has to follow these steps:

1. Define and implement a valid workflow

2. Submit the workflow components to the MedPerf server

3. Develop a demo dataset

4. Submit the benchmark to the MedPerf server

## Providing a Valid Workflow

This is accomplished by submitting three [MLCubes](../mlcubes.md):

1. **The Data Preparator MLCube:** This MLCube will be used to transform raw data into a dataset ready for the AI model execution. All data owners willing to participate in this benchmark should have their data prepared using this MLCube. Details on how to implement data preparation MLCubes and hosting their files can be found [here](https://github.com/aristizabal95/mlcube_examples/tree/medperf-examples/medperf/data_preparator).

2. **The Reference Model MLCube:** This MLCube will contain an example model implementation for the desired AI task. It should be compatible with the data preparation MLCube (i.e. the outputs of the data preparation MLCube can be directly fed as inputs to this MLCube). Details on how to implement model MLCubes and hosting their files can be found [here](https://github.com/aristizabal95/mlcube_examples/tree/medperf-examples/medperf/model).

3. **The Metrics MLCube:** This MLCube will be responsible for evaluating the performance of a model. It should be compatible with the reference model MLCube (i.e. the outputs of the reference model MLCube can be directly fed as inputs to this MLCube). Details on how to implement metrics MLCubes and hosting their files can be found [here](https://github.com/aristizabal95/mlcube_examples/tree/medperf-examples/medperf/metrics).

For this tutorial, these MLCubes are already implemented and hosted, and can be found here: [Data Preparator](https://github.com/aristizabal95/medical/tree/65a7d3f9d40a03c665616c96819d655e619421c1/cubes/xrv_prep), [Reference Model](https://github.com/aristizabal95/medical/tree/65a7d3f9d40a03c665616c96819d655e619421c1/cubes/xrv_chex_densenet), [Metrics](https://github.com/aristizabal95/medical/tree/65a7d3f9d40a03c665616c96819d655e619421c1/cubes/metrics).

Next, we are going to submit these MLCubes to the MedPerf server using MedPerf CLI.

## Submit the Workflow Components

An MLCube in MedPerf is recognized by a set of files. For our example:

1. The Data Preparator MLCube is identified by:

   1. The MLCube configuration file:

   2. The parameters file

2. The Reference Model MLCube is identified by:

   1. The MLCube configuration file:

   2. The parameters file:

   3. A tarball containing the model weights:

3. The Metrics MLCube is identified by:

   1. The MLCube configuration file:

   2. The parameters file

To submit these MLCubes:

```
medperf mlcube submit -n my-prep-cube -m <link> -p <link>
```

# TODO: Continue rephrasing from here

## Develop a Demo Dataset

In order to test the implementation of your MLCubes, as well as potentially allow other users to test their implementations for your benchmark, a public demonstration dataset should be hosted on the web. This demo dataset can be either a subset of a publicly accessible dataset, which you have clearance to provide or a synthetic dataset. It’s up to you what the contents of this dataset are.

**Note:** The demo dataset will be used as input to the data preparation cube as part of the compatibility testing.

Demo datasets must be compressed as a `.tar.gz` file, and at the root there should be a <strong><code>paths.yaml</code></strong> file with the following structure:

```
data_path: <DATA_PATH>
labels_path: <LABELS_PATH>
```

where:

- `data_path:` path relative to the location of the <strong><code>paths.yaml</code></strong> file that should be used as <code>data_path</code> input for the Data Preparator MLCube
- <code>labels_path:</code> path relative to the location of the <strong><code>paths.yaml</code></strong> file that should be used as <code>labels_path</code> input for the Data Preparator MLCube

<strong>If your some reason you can’t host your demo dataset</strong>, you can bypass the demo dataset retrieval by following the next steps:

1. Get the hash of your demo dataset tarball file with the following command

```
shasum demo_dataset.tar.gz
```

2. Create a folder with that hash under Medperf’s demo dataset filesystem
3. Move the tarball inside that folder and name it `tmp.tar.gz`

```
mv demo_dataset.tar.gz ~/.medperf/demo/<hash>/tmp.tar.gz
```

Keep in mind that your benchmark will only work for those that have done the same thing on their machines.

**Note:** These steps should be followed if you wish to test your implementation before submitting anything to the platform.

## Test Your Implementation

You can test your benchmark workflow before submitting anything to the platform. To do this, run the following command:

```
medperf test -p path/to/data_preparator/mlcube -m path/to/model/mlcube -e path/to/evaluator/mlcube -d <demo_dataset hash> <demo_datashet hash>
```

Once your tests are complete, you can continue with submitting your MLCubes and your benchmark.

## Submitting Your MLCubes

To submit your MLCube, you should have the following information at hand:

- <strong><code>mlcube.yaml</code></strong> raw github url with commit hash
- <strong><code>parameters.yaml</code></strong> raw github url with commit hash
- URL for the additional files tarball (optional)

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

## Submitting Your Benchmark

Once all your cubes are submitted to the platform, you can create your benchmark. For this, you need to keep at hand the following information:

- Data preparator UID (obtained through <strong><code>medperf mlcube ls</code></strong>)
- Reference model UID (obtained through <strong><code>medperf mlcube ls</code></strong>)
- Evaluator UID (obtained through <strong><code>medperf mlcube ls</code></strong>)
- Demo Dataset URL (if not hosted publicly, can be blank)
- Demo Dataset Hash (Only required if not hosted publicly)

You can create your benchmark using the following command:

```
medperf benchmark submit --name <benchmark_name> --description <benchmark_description> --demo-url <demo_url> --data-preparation-mlcube <data_preparator_MLCube_uid> --reference-model-mlcube <model_MLCube_uid> --evaluator-mlcube <evaluator_MLCube_uid>
```

If all the compatibility tests run successfully, the CLI will provide a response as follows:

```
MedPerf 0.0.0
Running compatibility test
Benchmark Data Preparation: tmp_1_2_3
> Preparation cube download complete
> MLCommons TorchXRayVision Preprocessor MD5 hash check complete
> Cube execution complete
> Sanity checks complete
> Statistics complete
Benchmark Execution: tmp_1_2_3
> Evaluator cube download complete
> MLCommons Metrics MD5 hash check complete
> Model cube download complete
> MLCommons TorchXRayVision CheXpert DenseNet model MD5 hash check complete
> Model execution complete
> Completed benchmark registration information
Submitting Benchmark to MedPerf
Uploaded
✅ Done!
```

In order to check the full list of arguments that you can provide, use the help command:

```
medperf benchmark submit --help
```

The CLI will return you the following response:

```
MedPerf 0.0.0
Usage: medperf [OPTIONS] COMMAND [ARGS]...

Options:
  --log TEXT                      [default: INFO]
  --log-file TEXT
  --comms TEXT                    [default: REST]
  --ui TEXT                       [default: CLI]
  --host TEXT                     [default: https://medperf.org]
  --storage TEXT                  [default: /Users/aristizabal-
                                  factored/.medperf]

  --certificate TEXT
  --local / --no-local            Run the CLI with local server configuration
                                  [default: False]

  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.

  --help                          Show this message and exit.

Commands:
  dataset  Manage datasets
  login    Login to the medperf server.
  mlcube   Manage mlcubes
  passwd   Set a new password.
  result   Manage results
  run      Runs the benchmark execution step for a given benchmark,
           prepared...
```

In addition, you can also see information about your benchmarks with:

```
medperf benchmark ls
```

The CLI will provide a list of your benchmarks and

```
MedPerf 0.0.0
  UID  Name    Description    State      Approval Status
-----  ------  -------------  ---------  -----------------
    7  dfci    submit         OPERATION  APPROVED
```

## Approving Additional Associations

You can retrieve all existing associations with:

```
medperf association ls
```

The CLI will return the existing associations:

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

In addition, you can filter associations to your benchmark by their approval status:

```
medperf association ls [pending | approved | rejected]
```

You can approve additional model associations with the following command:

```
medperf association approve -b <benchmark_uid> [-m <mlcube_uid>]
```

A similar approach is used for approving dataset associations:

```
medperf association approve -b <benchmark_uid> [-d <dataset_uid>]
```

If you can to reject an association, use the following command for rejecting a model

```
medperf association reject -b <benchmark_uid> [-m <model_uid>]
```

and the following one to reject a dataset association:

```
medperf association reject -b <benchmark_uid> [-m <dataset_uid>]
```

Then, the CLI will provide a response for approving or rejecting a benchmark as follows:

```
MedPerf 0.0.0
✅ Done!
```

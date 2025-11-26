# HEMnet pipeline

This pipeline runs the training data preparation procedure from [HEMnet](https://github.com/BiomedicalMachineLearning/HEMnet/tree/master). A modified version of their original [Docker image](https://hub.docker.com/layers/andrewsu1/hemnet/latest/images/sha256-5b371f828cfd41e223b46678cef157ec599847f17f0cf5711a0288908b287d5b) is used here, which splits the processing into separate steps that are chained together via CWL. This modified Docker image is available in DockerHub at [this link](https://hub.docker.com/r/mlcommons/hemnet-airflow), with the source code available in the `./project`subdirectory. The main modification of this version is splitting the pipeline into separate stages that can be executed by Airflow.

## 1. Get the HEMnet data

The data used for the HEMnet study is available on [this location](https://dna-discovery.stanford.edu/publicmaterial/web-resources/HEMnet/images/). The pipeline runs on pairs of TP53 and H&E (HandE suffix) slides. *The code does **NOT** check for valid pairings in inputs!* Make sure your input data is correctly formatted as shown below


```
.
svs
├── NNN_C_XXXX_Y_TP53.svs
├── NNN_C_XXXX_Y_HandE.svs
```

Where `NNN` and `XXXX`  ID numbers (`XXXX` may contain letters), `C` may be either equal to `T` (tumor) or `N` (non_tumor) and `Y` is a single digit number that may differ between slides of a given pair. For example, the structure below contains only valid input data pairings:

```
.
svs
├── 526_T_15907_2_TP53.svs
├── 526_T_15907_3_HandE.svs
├── 2065_N_127524A_2_HandE.svs
├── 2065_N_127524A_4_.TP53svs
├── 2171_T_11524A_2_HandE.svs
├── 2171_T_11524A_4_TP53.svs
```

While the example below is invalid. Notice the slightly different IDs in the pseudo-parings marked with (*) and (**).

```
.
svs
├── 526_T_15907_2_TP53.svs
├── 526_T_15907_3_HandE.svs
├── 2065_N_12752A_2_HandE.svs (*)
├── 2065_T_12756A_4_.TP53svs. (*)
├── 2171_N_11521A_2_HandE.svs (**)
├── 2171_T_11524A_4_TP53.svs (**)
```

### 2.1 Define the template slide
One of the slides used as input must be also used as the template slide. This template must be a copy of the original slide into the `templates` directory, inside the `svs` directory. The example below shows valid input using the `2171_T_11524A_4_TP53.svs` slide as the template slide:

```
.
svs
├──template
│  └── 2171_T_11524A_4_TP53.svs
├── 526_T_15907_2_TP53.svs
├── 526_T_15907_3_HandE.svs
├── 2065_N_127524A_2_HandE.svs
├── 2065_N_127524A_4_.TP53svs
├── 2171_T_11524A_2_HandE.svs
├── 2171_T_11524A_4_TP53.svs
```



## Appendix. Build the customized Docker image
From the directory of this README file, run the following commands
```shell
cd customized_image
docker build . -t local/hemnet:0.0.9
```
*NOTE!* If a different image tag is used, the CWL steps located at `./cwl/indivivdual_steps` must have their Docker requirements modified to match the name used.
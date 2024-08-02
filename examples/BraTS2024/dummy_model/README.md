# BraTS 2024 Dummy Models

Reference model MLCube for:

* [Meningioma Radiotherapy](https://www.synapse.org/Synapse:syn53708249/wiki/627503)
* [Pathology](https://www.synapse.org/Synapse:syn53708249/wiki/628091)

## Example model outputs

### Radiotherapy

A single folder with segmentation files, e.g.

```
predictions
├── BraTS-MEN-RT-xxxx-x.nii.gz
├── BraTS-MEN-RT-yyyy-y.nii.gz
└── BraTS-MEN-RT-zzzz-z.nii.gz
```

### Pathology

A 2-column CSV with `SubjectID` and `Prediction` as the headers, e.g.

```
SubjectID,Prediction
BraTSPath_cohort_xxxxxxx.png,A
BraTSPath_cohort_yyyyyyy.png,B
BraTSPath_cohort_zzzzzzz.png,C
```

where `A`, `B`, and `C` are integers from 0 to 5.

## Usage

> [!NOTE]
> For `PARAMETERS_FILE`, use `patameters-rt.yaml` for a radiotherapy
> dataset and `parameters-path.yaml` for pathology.

**Python**

```
python project/mlcube.py infer \
  --parameters_file mlcube/workspace/PARAMETERS_FILE \
  --data_path /path/to/prepared_data/ \
  --output_path predictions
```

**Docker**

```
docker run --rm \
  -v $PWD/mlcube/workspace/PARAMETERS_FILE:/parameters.yaml \
  -v /path/to/prepared_data:/data \
  -v $PWD/predictions:/predictions \
  ghcr.io/vpchung/brats2024-dummy-model:0.0.1 \
  infer --data_path /test_data  --parameters_file /parameters.yaml --output_path /predictions
```

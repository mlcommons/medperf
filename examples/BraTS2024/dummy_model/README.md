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

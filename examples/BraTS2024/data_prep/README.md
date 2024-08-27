# BraTS 2024 Data Preparation

Data preparation MLCube for the raw datasets of:

* [Meningioma Radiotherapy](https://www.synapse.org/Synapse:syn53708249/wiki/627503)
* [Pathology](https://www.synapse.org/Synapse:syn53708249/wiki/628091)

## Example raw datasets

### Radiotherapy

```
BraTS-MEN-RT/
├── BraTS-MEN-RT-xxxx-x
│   ├── BraTS-MEN-RT-xxxx-x_gtv.nii.gz
│   └── BraTS-MEN-RT-xxxx-x_t1c.nii.gz
├── BraTS-MEN-RT-yyyy-y
│   ├── BraTS-MEN-RT-yyyy-y_gtv.nii.gz
│   └── BraTS-MEN-RT-yyyy-y_t1c.nii.gz
└── BraTS-MEN-RT-zzzz-z
    ├── BraTS-MEN-RT-zzzz-z_gtv.nii.gz
    └── BraTS-MEN-RT-zzzz-z_t1c.nii.gz
```

where:
* `*_t1c.nii.gz` are data given to model MLCubes to make their inference
* `*_gtv.nii.gz` are the labels (groundtruth)

### Pathology

```
BraTS-Path/
├── BraTSPath_cohort_xxxxxxx.png
├── BraTSPath_cohort_yyyyyyy.png
├── BraTSPath_cohort_zzzzzzz.png
└── labels.csv
```

where:
* `*.png` are data given to model MLCubes to make their inference
* `labels.csv` are the classfication labels

## Example prepared datasets

### Radiotherapy

```
data
├── BraTS-MEN-RT-xxxx-x
│   └── BraTS-MEN-RT-xxxx-x_t1c.nii.gz
├── BraTS-MEN-RT-yyyy-y
│   └── BraTS-MEN-RT-yyyy-y_t1c.nii.gz
└── BraTS-MEN-RT-zzzz-z
    └── BraTS-MEN-RT-zzzz-z_t1c.nii.gz

labels
├── BraTS-MEN-RT-xxxx-x_gtv.nii.gz
├── BraTS-MEN-RT-yyyy-y_gtv.nii.gz
└── BraTS-MEN-RT-zzzz-z_gtv.nii.gz
```

### Pathology

```
data
├── BraTSPath_cohort_xxxxxxx.png
├── BraTSPath_cohort_yyyyyyy.png
└── BraTSPath_cohort_zzzzzzz.png

labels
└── labels.csv
```

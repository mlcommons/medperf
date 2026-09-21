# RANO mock reference model

A placeholder reference model for registering a RANO benchmark. It does **no real
inference** — for every `<subject>/<timepoint>` it finds in `data_path` (the shape
`prep_workflow`'s RANO preparator emits), it writes an all-background segmentation
volume with the same shape/affine as one of the input MRI volumes, named the way
[`examples/cc/rano/metrics_container_config.yaml`](../../cc/rano/metrics_container_config.yaml)'s
image (`mlcommons/rano-metrics`) expects raw predictions to be named:
`<subject>_<timepoint with dots replaced by underscores>.nii.gz` (see
`examples/cc/rano/implementation/benchmark/metrics/utils.py`'s `symlink_one_subject`,
which symlinks the real `..._final_seg.nii.gz` ground truth under that same
transformed name before comparing).

## Why this exists

The only pre-existing RANO reference model in this repo
([`examples/cc/rano/implementation/`](../../cc/rano/implementation)) is built for the
confidential-computing demo: it requires CUDA/GPU, is `FROM
mlcommons/medperf-confidential-benchmark-base`, and runs as an `ASSET`-type model
through MedPerf's `requires_cc()` execution path. That's the wrong shape for
registering a plain benchmark just to prove a data preparator works end-to-end
through the real MedPerf flow (register container → register benchmark → register
dataset → prepare → run).

This container exists only to satisfy that flow's mechanics — real filenames, real
volume mounts, a real evaluator run — without needing a trained segmentation model.
Every prediction is empty, so any score computed against it is meaningless.

## Build & test

```bash
docker build -t <your-dockerhub-user>/rano-mock-model:0.0.1 examples/RANO/mock_model
# update image: in container_config.yaml to match
```

`test.sh` runs `infer` against `./workspace/input_data` (real or fixture RANO-prep
output — subject/timepoint folders of `..._brain_<modality>.nii.gz` volumes) and
writes predictions to `./workspace/predictions`. See
[`prep_workflow/examples/rano/README.md`](../../../prep_workflow/examples/rano/README.md)
for how to get real prepared RANO output to test against.

```bash
bash test.sh
bash clean.sh   # removes generated predictions
```

To score the predictions with the real evaluator, run
`examples/cc/rano/metrics_container_config.yaml`'s `evaluate` task against
`./workspace/predictions` and the same dataset's `labels` output (nested
`<subject>/<timepoint>/<subject>_<timepoint>_final_seg.nii.gz`, same shape the
preparator writes) with `medperf container run_test`.

## Register

```bash
medperf container submit --name rano-mock-model \
  -m examples/RANO/mock_model/container_config.yaml \
  --operational
```

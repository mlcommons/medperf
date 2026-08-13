# RANO — ported to the in-container workflow engine

The full RANO brain-tumor preparation pipeline (from the `airflow` branch)
expressed with the in-container orchestrator instead of Airflow.

- `project/stages/`, `project/sanity_check.py`, `project/metrics.py` — the reused
  scientific stage code (copied verbatim from the branch). `stages/constants.py`
  and the heavy libraries/models are provided by the base image
  `mlcommons/rano-data-prep-mlcube:1.0.10`.
- `project/steps/rano_steps.py` — thin `Step` wrappers that construct and run each
  stage per subject (replacing the branch's `direct_stages.py` Typer commands).
- `project/conditions/conditions.py` — `AnnotationDone` / `BrainMaskChanged`,
  ported to the `Condition` interface (branching now lives in `workflow.yaml`, not
  inside the stages).
- `project/workflow.yaml` — the control graph: per-subject fan-out → manual-review
  branch (with a rollback cycle) → barrier → manual-approval gate → consolidation.

The workflow shape (graph + step/condition discovery) is validated by
`tests/test_examples.py`. The scientific stages are **not** executed here — they
need the base image, the nnU-Net models, and real DICOM data. Build and run with:

```bash
docker build -f examples/rano/Dockerfile -t mlcommons/rano-data-prep-workflow:0.1.0 .
# register examples/rano/container_config.yaml with MedPerf as a data preparator
```

## How to test

`test.sh` runs the built image locally with `medperf container run_test` (`prepare`
then `statistics`) against `./workspace`, without registering anything with MedPerf.
This requires the `mlcommons/rano-data-prep-mlcube` base image to build and real
DICOM data to run — neither is provided in this repo, so `test.sh` won't run out
of the box.

1. Update `image:` in `container_config.yaml` to match the tag you built.
2. Set up `./workspace`:
   ```bash
   mkdir -p workspace/input_labels workspace/metadata
   # workspace/input_data must contain <subject>/<timepoint>/ sub-directories
   # of real DICOM/NIfTI scans (see Setup in project/steps/rano_steps.py).
   cp -r <your-subjects>/* workspace/input_data/
   echo "{}" > workspace/parameters.yaml   # replace with your real params
   # TumorExtraction reads model weights from additional_files/models — see
   # rano_steps.py — so tumor extraction will fail without this:
   mkdir -p workspace/additional_files/models
   cp -r <your-nnUNet_trained_models> workspace/additional_files/models/nnUNet_trained_models
   ```
3. `bash test.sh` — `prepare` writes `workspace/data` / `workspace/labels` /
   `workspace/metadata` / `workspace/report.yaml`; `statistics` reads
   `data`/`labels` back and writes `workspace/statistics.yaml`. Logs land next
   to the script as `logs_prepare.log` / `logs_statistics.log`.
4. `bash clean.sh` removes the generated outputs so `prepare` can be re-run
   from a clean state; `input_data`, `input_labels` and `parameters.yaml` are
   left untouched.

To point at different locations, edit the `--mounts` key=value pairs in
`test.sh` — each key must match a volume declared under the task's
`input_volumes`/`output_volumes` in `container_config.yaml`. Exception:
`parameters_file` and `additional_files` aren't set via `--mounts` (see the
top-level README's "Test locally" section) — `test.sh` already passes them
via `--parameters_file_path` / `--additional_files_path`.

## Mapping from the Airflow workflow

| Airflow step (`command`)        | Ported step (`workflow.yaml` id / class) |
|---------------------------------|------------------------------------------|
| `initial_setup`                 | `setup` / `Setup`                        |
| `make_csv`                      | `make_csv` / `MakeCsv`                    |
| `convert_nifti`                 | `convert_nifti` / `ConvertNifti`         |
| `extract_brain`                 | `brain_extraction` / `BrainExtraction`   |
| `extract_tumor`                 | `tumor_extraction` / `TumorExtraction`   |
| `prepare_for_manual_review`     | `manual_review` / `PrepareForReview`     |
| `rollback_to_brain_extract`     | `rollback` / `Rollback`                  |
| `segmentation_comparison`       | `segmentation_comparison` / `SegmentationComparison` |
| `calculate_changed_voxels`      | `calculate_changed_voxels` / `CalculateChangedVoxels` (barrier) |
| `final_confirmation`            | `final_confirmation` (type: manual_approval) |
| `move_labeled_files`            | `move_labeled_files` / `MoveLabeledFiles` (barrier) |
| `consolidation_stage`           | `consolidate` / `Consolidate` (barrier, terminal) |
| `sanity_check` / `metrics`      | validation flow (`SanityCheck` → `Statistics`) |

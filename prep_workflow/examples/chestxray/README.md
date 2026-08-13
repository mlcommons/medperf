# ChestXRay tutorial — ported to the in-container workflow engine

A minimal, linear port of the ChestXRay tutorial preparator. The tutorial's
`prepare` / `sanity_check` / `statistics` functions are reused verbatim (under
`project/science/`) and wrapped as barrier `Step`s — ChestXRay prepares the whole
dataset in one pass, so there is no per-subject fan-out.

```bash
docker build -f examples/chestxray/Dockerfile -t mlcommons/chestxray-prep-workflow:0.1.0 .
# register examples/chestxray/container_config.yaml with MedPerf
```

## How to test

`test.sh` runs the built image locally with `medperf container run_test` (`prepare`
then `statistics`) against `./workspace`, without registering anything with MedPerf.

1. Update `image:` in `container_config.yaml` to match the tag you built.
2. Set up `./workspace`:
   ```bash
   cd examples/chestxray
   mkdir -p workspace
   cp -r ../../../medperf_tutorial/sample_raw_data/images workspace/input_data
   cp -r ../../../medperf_tutorial/sample_raw_data/labels workspace/input_labels
   cp ../../../medperf_tutorial/data_preparator/workspace/parameters.yaml workspace/parameters.yaml
   ```
   That reuses the same sample chest-x-ray images/labels and `parameters.yaml`
   (label list, image/label CSV columns, output image size) as the ChestXRay
   tutorial. Swap in your own PNGs + `labels.csv` (same columns) to test with
   different data, or edit `workspace/parameters.yaml`.
3. `bash test.sh` — `prepare` writes `workspace/data` / `workspace/labels` /
   `workspace/report.yaml`; `statistics` reads those back and writes
   `workspace/statistics.yaml`. Logs land next to the script as
   `logs_prepare.log` / `logs_statistics.log`.
4. `bash clean.sh` removes the generated outputs so `prepare` can be re-run
   from a clean state; `input_data`, `input_labels` and `parameters.yaml` are
   left untouched.

To point at different locations, edit the `--mounts` key=value pairs in
`test.sh` — each key must match a volume declared under the task's
`input_volumes`/`output_volumes` in `container_config.yaml`. Exception:
`parameters_file` isn't set via `--mounts` (see the top-level README's
"Test locally" section) — `test.sh` already passes it via
`--parameters_file_path`.

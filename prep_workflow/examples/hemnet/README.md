# HEMnet — ported to the in-container workflow engine

The HEMnet histopathology pipeline (from the `airflow` branch) expressed with the
in-container orchestrator. The reused HEMnet scripts (`project/science/*.py`) are
invoked as subprocesses from their working directory in the image; slides are
registered as subjects and flow per-subject through registration/masking/tiling,
with barrier steps for normalisation, consolidation and cleanup.

Note: the reference Airflow version passed `--partition` to scripts that actually
expect `-s/--subject-subdir`; this port uses the correct flag. Requires the
`andrewsu1/hemnet` base image and real `.svs` slides; not executed here.

```bash
docker build -f examples/hemnet/Dockerfile -t mlcommons/hemnet-prep-workflow:0.1.0 .
# register examples/hemnet/container_config.yaml with MedPerf
```

## How to test

`test.sh` runs the built image locally with `medperf container run_test` (`prepare`
then `statistics`) against `./workspace`, without registering anything with MedPerf.
This requires the `andrewsu1/hemnet` base image to build and real `.svs` slides to
run — neither is provided in this repo, so `test.sh` won't run out of the box.

1. Update `image:` in `container_config.yaml` to match the tag you built.
2. Set up `./workspace`:
   ```bash
   mkdir -p workspace/input_labels
   # workspace/input_data must contain paired *_TP53*.svs / *_HandE*.svs slides
   # (see DiscoverSlides in project/steps/hemnet_steps.py) — real data only.
   cp <your-slides>/*.svs workspace/input_data/
   echo "{}" > workspace/parameters.yaml   # replace with your real params
   ```
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
`--parameters_file_path`. `container_config.yaml` also declares an
`additional_files` volume for parity with the other examples' `/workspace`
layout, but the HEMnet steps don't currently read it.

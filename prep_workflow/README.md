# prep-workflow — in-container data-preparation workflow engine

A small orchestration engine that runs a **multi-step, per-subject data-preparation
workflow inside a single container**. To MedPerf it looks like an ordinary
`DockerImage` data preparator whose single executable runs preparation by
default. MedPerf then invokes `statistics` with `--start=sanity_check` to
run sanity checking and statistics, so no MedPerf CLI or server changes are needed. Already-prepared datasets skip the first run.
Inside, the
engine runs many steps per subject, in parallel, with branching and human review.

## Why in-container?

Spawning a container per step per subject re-pays interpreter/CUDA/model-load
startup thousands of times (e.g. 500 subjects × 10 steps) and can't pipeline a
human-in-the-loop step (subject A being annotated while subject B keeps computing).
Running the orchestration inside one warm container fixes both.

## What an author writes

Only four things (everything else is provided):

```
project/
├── steps/         # Step subclasses (any number of files / classes)
├── conditions/    # Condition subclasses used for branching
├── workflow.yaml  # the step graph (which step follows which, and when)
└── requirements.txt
```

### Steps

```python
from prep_workflow import Step

class Convert(Step):
    per_subject = True            # runs once per subject (default). False = barrier.
    def run(self, ctx):
        # ctx.subject, ctx.paths.*, ctx.params, ctx.report, ctx.logger
        ...                        # raise to signal failure
```

### Conditions (for branching)

```python
from prep_workflow import Condition

class AnnotationDone(Condition):
    def evaluate(self, ctx) -> bool:
        ...
```

### workflow.yaml

```yaml
max_workers: 4
steps:
  - id: discover                  # first step must be a barrier that lists subjects
    step: DiscoverSubjects        # a built-in; or write your own barrier step
    per_subject: false
    next: convert
  - id: convert
    step: Convert
    per_subject: true
    limit: 4                      # max concurrent subjects in this step
    next: review
  - id: review
    step: PrepareForReview
    per_subject: true
    next:                         # branch on conditions
      if:
        - condition: AnnotationDone
          target: finalize
      else: review                # loop: wait `wait`s and re-check (step not re-run)
      wait: 60
  - id: finalize
    step: Finalize
    per_subject: false            # barrier: runs once after all subjects arrive
    next: sanity_check            # keep the graph continuous; prepare still stops here
  - id: sanity_check              # --start=sanity_check begins here
    step: SanityCheck
    per_subject: false
    next: statistics
  - id: statistics
    step: Statistics
    per_subject: false
    next: null
```

Starts are conventional: preparation begins at the first step and stops before
`sanity_check` even when the YAML keeps `next: sanity_check` for readability;
`--start=sanity_check` begins at step id `sanity_check` and must reach
`SanityCheck` and `Statistics`. `next` is a step id, `null` (terminal), or a
branch (`if` / `else` / `wait`). A branch target pointing at an earlier step
forms a retry cycle. `on_error: ignore` skips a failed subject instead of
stopping the run.

Built-ins: `DiscoverSubjects` (one subject per input sub-dir; `config: {single: true}`
for a single-token dataset) and `ManualApproval` (`type: manual_approval` — a barrier
that waits for a confirmation marker file).

## Progress reporting

The engine continuously writes a per-subject `report.yaml` in the exact shape
MedPerf already ships, so `medperf dataset prepare` streams live progress with no
extra work.

## Build & run

```bash
./template/build.sh my-org/my-data-prep:0.0.1     # builds the image
# then register the container_config.yaml with MedPerf as a normal data preparator
```

## Test locally

Before registering with MedPerf, run the built image directly with
`medperf container run_test` — the same developer utility used by every other
MedPerf container example (see e.g. `examples/fl/prep/test.sh`). `template/test.sh`
does this for you: it runs `prepare` then `statistics` against local folders
under `template/workspace/`, exactly the way MedPerf would run them.

1. Update `image:` in `container_config.yaml` to match the tag you built (or
   leave `my-org/my-data-prep:0.0.1` if that's what you used).
2. Set up `template/workspace/`:
   ```bash
   mkdir -p template/workspace/input_data/subject1 template/workspace/input_labels
   cp <your-raw-files-for-subject1> template/workspace/input_data/subject1/
   # repeat for as many workspace/input_data/<subject-id>/ folders as you want
   # to test with — DiscoverSubjects registers one subject per sub-directory.
   echo "{}" > template/workspace/parameters.yaml   # replace with your real params
   # optional: drop any extra files your steps need (e.g. model weights) into
   # template/workspace/additional_files/ — test.sh already mounts it via
   # --additional_files_path.
   ```
3. Run it:
   ```bash
   bash template/test.sh
   ```
   `prepare` writes into `workspace/data` / `workspace/labels` (plus
   `workspace/metadata` and `workspace/report.yaml`); `statistics` then reads
   those as its input and writes `workspace/statistics.yaml`. Logs land next to
   the script as `logs_prepare.log` / `logs_statistics.log`.
4. `bash template/clean.sh` removes the generated outputs (`data`, `labels`,
   `metadata`, `report.yaml`, `statistics.yaml`) so you can re-run `prepare`
   from a clean state — your `input_data`, `input_labels` and `parameters.yaml`
   are left untouched.

To point the test at different locations (or add volumes you've added to
`container_config.yaml`), edit the `--mounts` key=value pairs in `test.sh`
directly — each key must match a volume name declared under the task's
`input_volumes`/`output_volumes` in `container_config.yaml`. Two volumes are
the exception: `parameters_file` and `additional_files` are never set via
`--mounts` — a key by either of those names there is silently ignored,
because `medperf container run_test` always overrides them from its own
`--parameters_file_path` / `--additional_files_path` flags (see
`cli/medperf/entities/cube.py`'s `extra_mounts`). `test.sh` already passes
`--parameters_file_path`; add `--additional_files_path` too if your task
declares an `additional_files` volume (see `examples/rano/test.sh`).

## Develop / test the engine

```bash
pip install -e .[test]
pytest
```

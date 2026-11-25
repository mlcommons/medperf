# Running MedPerf on a Slurm Cluster

MedPerf can submit container tasks (`prepare`, `sanity_check`, `statistics`, `infer`, `evaluate`, ...) to a Slurm cluster instead of running them on the machine where `medperf` runs. This is meant for HPC systems such as JSC JUPITER, where:

- you run `medperf` on a **login node**,
- Docker is not available, and Apptainer/Singularity is,
- heavy work must run on **compute nodes** through the Slurm scheduler.

## How it works

Two independent settings control container execution:

| Setting | Values | Decides |
|---|---|---|
| `platform` | `docker`, `singularity` | **how** the container is run |
| `launcher` | `local` (default), `slurm` | **where** the container is run |

With `--launcher slurm`, MedPerf still downloads and converts container images on the login node, because compute nodes usually have no internet access. Only the container run itself is submitted with `sbatch`. MedPerf then waits for the job and streams its log, and it marks the task as finished or failed exactly as it does for a local run.

`--launcher slurm` requires `--platform singularity`. Docker containers are started by the Docker daemon, outside the Slurm job, so Slurm can neither confine nor track them.

## Requirements

- `sbatch`, `squeue` and `scancel` on the machine running `medperf` (a Slurm submit host). `sacct` is used when available but is not required.
- `apptainer` or `singularity` on both the login node and the compute nodes.
- A **filesystem shared between the login node and compute nodes** for:
    - MedPerf storage (`~/.medperf` by default; relocate it with `medperf storage move -t <path>`),
    - the Slurm jobs directory (`~/.medperf_logs/slurm_jobs` by default),
    - your datasets.

    Node-local paths such as `/tmp` will not work.
- Container images built for the compute nodes' CPU architecture. JUPITER's nodes are Arm (aarch64), so `amd64`-only images will not run there. MedPerf reads each image's architecture before submitting, and refuses images that don't match (see `--slurm-node-arch`).

## Configuration

| Option | Profile key | Meaning | Default |
|---|---|---|---|
| `--launcher` | `launcher` | `local` or `slurm` | `local` |
| `--slurm-partition` | `slurm_partition` | `sbatch --partition` | cluster default |
| `--slurm-account` | `slurm_account` | `sbatch --account` (budget/project) | cluster default |
| `--slurm-time` | `slurm_time` | `sbatch --time`, e.g. `02:00:00`, `1-00:00:00` | cluster default |
| `--slurm-cpus-per-task` | `slurm_cpus_per_task` | `sbatch --cpus-per-task` | cluster default |
| `--slurm-mem` | `slurm_mem` | `sbatch --mem`, e.g. `64G` | cluster default |
| `--slurm-gres` | `slurm_gres` | `sbatch --gres`, e.g. `gpu:4` | cluster default |
| `--slurm-extra-args` | `slurm_extra_args` | other `sbatch` options, e.g. `"--qos=normal"` | none |
| `--slurm-setup-commands` | `slurm_setup_commands` | shell lines run in the job before the container, e.g. `module load ...` | none |
| `--slurm-jobs-dir` | `slurm_jobs_dir` | where job scripts and logs are written (must be shared) | `~/.medperf_logs/slurm_jobs` |
| `--slurm-node-arch` | `slurm_node_arch` | compute nodes' CPU architecture (e.g. `aarch64`); images are checked against it before submission | the login node's architecture |
| `--slurm-poll-interval` | `slurm_poll_interval` | seconds between status checks | `30` |
| `--slurm-accounting-grace` | `slurm_accounting_grace` | seconds to wait for a job that left the queue but has no accounting record or exit code yet | `300` |

MedPerf never invents resource values. Anything you leave unset is omitted from the job, and the cluster's defaults apply. Every job requests `--nodes=1 --ntasks=1` (a MedPerf container is one process) and `--no-requeue`.

Options can be stored in a profile:

```bash
medperf profile set --platform singularity --launcher slurm \
  --slurm-account <budget> --slurm-partition booster --slurm-time 02:00:00 \
  --slurm-gres gpu:4 --gpus all
```

or passed for a single command, before the command name:

```bash
medperf --slurm-time 08:00:00 dataset prepare --data_uid 12
```

### GPUs

GPU access has two separate parts:

1. **Slurm allocates GPUs to the job.** Use `--slurm-gres gpu:N`, or the site's equivalent through `--slurm-extra-args`.
2. **The container is given access to them.** Use `--gpus all`, which adds `--nv`. The GPUs Slurm assigned (`CUDA_VISIBLE_DEVICES`) are forwarded into the container.

Specific device IDs (`--gpus device=0,1`) are rejected with the Slurm launcher, because device numbering is decided by Slurm on the compute node. MedPerf warns when only one of the two parts is configured.

### Container environment

A container gets exactly the environment variables listed as `export` lines in its `job.sh`: those from its container config, those MedPerf sets for the task, and `PYTHONUNBUFFERED=1`. `SINGULARITYENV_*` / `APPTAINERENV_*` variables in the shell where you run `medperf` are not passed to jobs. To give jobs an extra variable, export it in `--slurm-setup-commands`, e.g. `--slurm-setup-commands "export SINGULARITYENV_MY_VAR=value"`.

## Running and monitoring tasks

Commands are used exactly as without Slurm. For example:

```text
$ medperf --platform singularity --launcher slurm benchmark run -b 1 -d 5
> Submitted Slurm job 4211873 for task 'infer'
> Job log: /p/home/jusers/me/jupiter/.medperf_logs/slurm_jobs/20261011-142501_medperf-infer_k3j9/job.log
```

*(Illustrative output.)*

While the job waits in the queue, the spinner shows its state and pending reason (`Slurm job 4211873 is pending (reason: Priority)`). Once it runs, the container's output is streamed to your terminal as it is written: MedPerf reads new lines from the job log every 2 seconds, and checks the job's state every `--slurm-poll-interval` seconds. Containers get `PYTHONUNBUFFERED=1`, so Python output reaches the log line by line, not in large buffered chunks.

`medperf` must keep running until the job finishes, because it is what collects the result and reports it. On a login node, run it inside `tmux` or `screen` so that a dropped SSH connection does not stop it.

## Logs

Each submission gets its own directory under the jobs directory:

| File | Content |
|---|---|
| `job.sh` | the generated batch script (can be resubmitted manually with `sbatch job.sh` for debugging) |
| `job.log` | stdout and stderr of the job: MedPerf's `MEDPERF-SLURM:` markers and the container's output |
| `exit_code` | exit code of the container, written by the job script |
| `medperf_status.json` | job ID, final Slurm state, exit code and MedPerf's verdict |

The container output is also copied to the usual MedPerf task log (for example `~/.medperf/experiments_logs/...`). MedPerf never deletes job directories, so remove old ones yourself when you no longer need them.

## Cancelling

- **Ctrl+C** in the terminal, or **Stop** in the WebUI, cancels the job with `scancel <jobid>`, targeting only that job ID.
- If `medperf` is killed without a chance to clean up (`kill -9`, or the login node rebooting), the job keeps running. Find and cancel it with:

```bash
squeue --me --name=medperf-infer
scancel <jobid>
```

## Timeouts

There are two different limits:

- `--slurm-time` is the **scheduler's** wall-time limit. Slurm stops the job when it is reached, and MedPerf reports `reached its Slurm time limit`.
- The existing MedPerf timeouts (`--infer_timeout`, `--prepare_timeout`, ...) limit how long the job may **run**, as seen by MedPerf. Time spent pending in the queue does not count. When exceeded, MedPerf cancels the job.

## Limitations

- `medperf` blocks while the job runs. There is no submit-and-detach mode yet.
- One Slurm job per container task. All tasks of one command use the same resource settings (there are no per-task overrides yet).
- Tasks that publish network ports (the training aggregator, `get_server_cert`) are rejected with `--launcher slurm`. Tasks that need outbound network access (certificate retrieval, training) are submitted with a warning, and will fail on clusters whose compute nodes have no internet. Run those with `--launcher local`.
- `--platform docker` cannot be combined with `--launcher slurm`.
- On clusters that allocate whole nodes (such as JUPITER), every task is charged as at least one full node for its run time, however small the task is.

## Testing

Unit tests mock all Slurm commands. The integration tests run real job scripts through a fake Slurm (`cli/medperf/tests/slurm/fake_slurm.py`):

```bash
cd cli/medperf/tests && pytest slurm
# also run a real container through the fake Slurm:
MEDPERF_SLURM_TEST_SIF=/path/to/any.sif pytest slurm
```

These tests do not prove the integration works on a real cluster. Use the checklist below for that.

## Validating on a real cluster (JUPITER checklist)

1. **Access:** you can SSH to a login node, `jutil user projects` lists your project, and `id` shows the `container` group (requested in JuDoor).
2. **Tools:** `which sbatch squeue sacct scancel apptainer` on the login node, and `sacct -j <any old job>` returns data. If not, note that MedPerf falls back to the exit code file.
3. **Shared storage:** move MedPerf storage to a directory under `$PROJECT` with `medperf storage move -t $PROJECT/medperf`. Confirm that a compute node sees it:
    `srun -A <budget> -p booster -N1 -t 5 ls <path>`
4. **Images:** fetch the benchmark containers once with `--launcher local --platform singularity` (or a `medperf` command that downloads them). Check that each image runs on Arm:
    `apptainer exec <image.sif> uname -m` should print `aarch64`.
5. **First job:** run a compatibility test, which submits `prepare`, `sanity_check`, `statistics`, `infer` and `evaluate` jobs on the benchmark's demo data: `medperf --launcher slurm --slurm-account <budget> --slurm-time 00:30:00 test run -b <benchmark_uid>`. Then:
    - `squeue --me` shows `medperf-<task>` jobs,
    - `job.log` contains `started on <compute node>`, not a login node,
    - `medperf_status.json` says `COMPLETED` with exit code `0`.
6. **Failures:** check that each case is reported correctly:
    - `--slurm-time 1`: a long task is reported as a time-limit failure,
    - Ctrl+C on a pending job: `sacct -j <id>` shows `CANCELLED`,
    - a wrong `--slurm-account`: the `sbatch` rejection message is shown.
7. **GPUs:** run with `--gpus all --slurm-gres gpu:4` and confirm that the container sees 4 GPUs. JSC documents that single-task jobs may see only one GPU. If that happens, add `--slurm-setup-commands "export CUDA_VISIBLE_DEVICES=0,1,2,3"`.

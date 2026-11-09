# BioML-bench on MedPerf

This example runs two [BioML-bench](https://github.com/science-machine/biomlbench) tasks as MedPerf benchmarks, with BioML-bench's own AIDE agent as the model under test. It is set up for JUPITER: the images are built for `linux/arm64` (GH200 nodes), and the commands use MedPerf's Singularity platform and Slurm launcher.

Everything a benchmark needs is here, in the layout of `examples/chestxray_tutorial`: the data, the data preparator, the reference model, the evaluator (metrics) and a model to evaluate.

## How BioML-bench maps onto MedPerf

BioML-bench downloads each task's raw data, runs the task's `prepare.py` to split it into what the agent sees and the hidden answers, and scores the agent's submission with the task's `grade.py`, ranking it on the task's leaderboard. Here:

| BioML-bench | MedPerf | Folder |
| --- | --- | --- |
| download the raw data | done once with `fetch_task.sh`; the result is in this folder | `tasks/<task>/raw/` |
| `prepare.py` (raw → `public/` + `private/`) | data preparator, `prepare`: `public/` becomes the dataset's data, `private/` its labels | `data_preparator/` |
| none | data preparator, `sanity_check` and `statistics` | `data_preparator/` |
| the Dummy agent (submits `sample_submission.csv`) | the reference model | `model_dummy/` |
| `grade.py` and the leaderboard ranking | the evaluator | `metrics/` |
| the AIDE agent (`agents/aide`) | a model, with its LLM served by vLLM inside the container | `model_aide/` |

The data preparator and the evaluator install BioML-bench, pinned to one commit, and run the task's own code. Nothing needs BioML-bench installed on the host.

## Contents

| Path | Purpose |
| --- | --- |
| `tasks/<task>/` | One task: its raw dataset, demo dataset, leaderboard and parameters (see below) |
| `common/` | Shared by the data preparator and the evaluator: the code that runs BioML-bench tasks offline (`biomlbench_task.py`), the Python packages, and what replaces the two packages without arm64 wheels (see below). `check_platform.py` is used by every image build |
| `data_preparator/` | `prepare`, `sanity_check`, `statistics`. Also holds `fetch.py`, which downloads a task |
| `metrics/` | `evaluate`: the task's score, and its rank on the leaderboard |
| `model_dummy/` | The reference model |
| `model_aide/` | The AIDE agent, with vLLM and an LLM (Qwen2.5-Coder-7B-Instruct) |
| `build.sh` | Builds the images for arm64 and pushes them |
| `fetch_task.sh` | Downloads another BioML-bench task into `tasks/` |
| `test/run_workflow.sh` | Runs prepare, sanity check, statistics, the Dummy model and the evaluation with Docker, without MedPerf |

## The tasks

Both are from BioML-bench's paper set (v0.1a), and among its smallest: a few hundred molecules (SMILES strings), under 200 KB each.

| Task | Id | Train / test | Metric | Dummy model's score |
| --- | --- | --- | --- | --- |
| `tasks/tdcommons-caco2-wang` | `polarishub/tdcommons-caco2-wang` | 728 / 182 | mean absolute error (lower is better) | 5.328 |
| `tasks/tdcommons-herg` | `polarishub/tdcommons-herg` | 523 / 132 | ROC-AUC (higher is better) | 0.5 |

Each task folder holds:

| File | What it is | Who uses it |
| --- | --- | --- |
| `raw/data/` | The raw dataset: the train and test tables, and a saved copy of the task's Polaris benchmark (`polaris_benchmark/`) | Data owner: `medperf dataset submit -d` |
| `raw/labels/` | Empty: the answers are in the raw data, and `prepare` splits them out | Data owner: `medperf dataset submit -l` |
| `parameters.yaml` | The task id, e.g. `task_id: polarishub/tdcommons-caco2-wang` | Benchmark owner: parameters of the data preparator and the evaluator |
| `demo_data.tar.gz` | The raw dataset plus `paths.yaml` | Benchmark owner: the benchmark's demo dataset |
| `metrics_additional_files.tar.gz` | The task's leaderboard (`leaderboard.csv`, 10 entries) | Benchmark owner: additional files of the evaluator |

The task code loads the Polaris benchmark both when preparing and when grading. Inside MedPerf, where there is no network, it gets the saved copy instead of the Polaris Hub.

The demo dataset is the whole raw dataset: the task is small, and Polaris checks the predictions against the full test set, so a smaller sample couldn't be graded.

To add another task, e.g. `polarishub/tdcommons-lipophilicity-astrazeneca`, run `bash fetch_task.sh <task id>`. It needs network access and an image of the data preparator that runs on your machine (see the script).

## The AIDE agent

`model_aide/` runs [AIDE](https://github.com/AIxBio/aideml_bmlb) as BioML-bench's `agents/aide/start.sh` does. BioML-bench runs it with OpenAI's API; here the LLM runs in the container:

1. vLLM serves the LLM on `localhost`, from weights in the model's additional files.
2. The agent gets BioML-bench's instructions, AIDE's notes (time and step limits) and the task's `description.md`. The instructions are BioML-bench's, with the paths changed to AIDE's `./input/` and `./submission/`, and without the points that don't apply offline (the validation server, installing packages).
3. AIDE runs within the time limit, writing and running solution scripts. It keeps the submission of its best solution so far.
4. That submission becomes the predictions. The agent's logs and best solution are saved next to it, in `agent_logs/`.

The container runs without network access, like every MedPerf container.

`model_aide/workspace/parameters.yaml` sets the LLM (weights folder, context length, GPU memory share, extra `vllm serve` options) and AIDE's limits. They are small by default, for a quick run: 20 steps and 1 hour, where BioML-bench used 2000 steps and 12 hours.

The weights are not in the image. `model_aide/workspace/additional_files/download.sh` downloads Qwen2.5-Coder-7B-Instruct (about 15 GB, Apache 2.0) from Hugging Face. To use another LLM, download it to a folder there and set `llm.weights` to that folder.

AIDE's solutions run on the CPUs, with scikit-learn, LightGBM, XGBoost, RDKit, PyTorch (CPU build) and others. The GPU runs the LLM.

The agent has its own Python, separate from vLLM's, so neither can break the other's packages.

## Requirements

- MedPerf on a JUPITER login node, with Apptainer (or Singularity) available there and on the compute nodes
- A Docker Hub account to push the images to, if you rebuild them
- Somewhere to host the demo dataset, the leaderboard and the LLM's weights by URL. The task files are small and are in this folder: once it is pushed to GitHub, their raw URLs work (see below)

## 1. Build and push the images

The container configs use `mhmdk0/bioml-bench-{prep,metrics,dummy}:0.0.1` and `mhmdk0/bioml-bench-aide:0.0.2`, built for `linux/arm64`. To rebuild them:

```bash
cd examples/bioml_bench
docker login
bash build.sh prep metrics dummy
TAG=0.0.2 bash build.sh aide
```

Set `REGISTRY` to push elsewhere, then change `image:` in the four `container_config.yaml` files.

Building needs no emulation, and for the AIDE image no copy of its vLLM base image (about 12 GB): the Python packages are installed on your machine for arm64 and copied onto the base images. The AIDE image is about 12 GB compressed. All but about 330 MB of it is the vLLM base, which Docker Hub shares with `vllm/vllm-openai`, so only that is uploaded.

Each tag holds one platform. MedPerf's Singularity runner reads an image's hash from Docker Hub as a plain image manifest, which a multi-platform tag doesn't have.

The builds install wheels only, except for a few pure Python packages: a package compiled on the build machine would be compiled for its CPU, not the image's. Each build also checks that every compiled file is for the image's CPU (`common/check_platform.py`).

Two packages that polaris-lib 0.13.0 needs have no Linux arm64 wheel (`common/overrides.txt`):

- `fastpdb` is left out. polaris imports it, but uses it only to read and store protein structures (PDB files), which these tasks don't have. A stand-in (`common/fastpdb/`) raises an error if it is ever used.
- `numcodecs` 0.15.1 comes from conda-forge's arm64 build instead of PyPI, checked against its SHA-256 hash (`common/install_conda_package.py`). Newer numcodecs has arm64 wheels, but doesn't work with zarr 2, which polaris needs. The conda-forge build needs only glibc 2.17.

## 2. Check the workflow locally (optional)

On a machine with Docker:

```bash
bash test/run_workflow.sh tasks/tdcommons-caco2-wang
```

This builds the data preparator, evaluator and Dummy images for your machine (tagged `:local`), then runs prepare, sanity check, statistics, the Dummy model and the evaluation as MedPerf runs them: as your user, with read-only inputs and no network. It prints the statistics and the results.

The AIDE agent needs a GPU for vLLM. To test the rest of it without one, build it for your machine on a small base image, and point it at any OpenAI-compatible server with `BIOML_AGENT_TEST_LLM_URL`. It then skips starting vLLM:

```bash
docker buildx build --builder default --load --build-arg VLLM_IMAGE=ubuntu:22.04 \
    -t bioml-bench-aide:test -f model_aide/Dockerfile .
docker run --rm -u $(id -u):$(id -g) --network host -e BIOML_AGENT_TEST_LLM_URL=http://127.0.0.1:8000 \
    -v <prepared data>:/mlcommons/volumes/data:ro \
    -v $PWD/model_aide/workspace/parameters.yaml:/mlcommons/volumes/parameters/parameters_file.yaml:ro \
    -v <empty folder>:/mlcommons/volumes/additional_files:ro \
    -v <output folder>:/mlcommons/volumes/predictions \
    bioml-bench-aide:test
```

The prepared data is the `data` folder in the working folder `run_workflow.sh` prints.

## 3. Set up MedPerf for JUPITER

Run the containers with Singularity, as Slurm jobs:

```bash
medperf profile set --platform singularity --launcher slurm \
    --slurm-account <budget> --slurm-partition <partition> \
    --slurm-time 02:00:00
```

The Dummy model, the data preparator and the evaluator don't use the GPU. The AIDE agent needs one GPU, for at least its `aide.time_limit` plus the time to load the LLM: about 1 h 15 min with the default parameters. Request the GPU only on the commands that run the agent (`model associate` in step 6, and `run` in step 7), by putting `--slurm-gres gpu:1` right after `medperf`, e.g. `medperf --slurm-gres gpu:1 run ...`.

## 4. Benchmark owner: register the containers and the benchmark

The URLs below are the files in this folder, on GitHub. Replace `<repo>` and `<branch>` with where it is pushed, e.g. `mhmdk0/medperf` and `bioml-bench`:

```bash
TASK=tdcommons-caco2-wang          # or tdcommons-herg
FILES=https://raw.githubusercontent.com/<repo>/<branch>/examples/bioml_bench/tasks/$TASK

medperf container submit -n bioml-$TASK-prep \
    -m data_preparator/container_config.yaml -p tasks/$TASK/parameters.yaml

medperf container submit -n bioml-$TASK-metrics \
    -m metrics/container_config.yaml -p tasks/$TASK/parameters.yaml \
    -a $FILES/metrics_additional_files.tar.gz

medperf model submit -n bioml-$TASK-dummy -m model_dummy/container_config.yaml

medperf benchmark submit -n bioml-$TASK \
    -d "BioML-bench task $TASK" \
    --demo-url $FILES/demo_data.tar.gz \
    -p <prep container UID> -m <dummy model UID> -e <metrics container UID>
```

`benchmark submit` runs the compatibility test: it prepares the demo dataset, runs the Dummy model on it and evaluates the predictions. The benchmark then waits for a MedPerf admin to approve it.

The benchmark owner also approves each dataset and model association request:

```bash
medperf association approve -b <benchmark UID> -d <dataset UID>
medperf association approve -b <benchmark UID> -m <model UID>
```

## 5. Data owner: register the dataset

```bash
medperf dataset submit -b <benchmark UID> \
    -d tasks/$TASK/raw/data -l tasks/$TASK/raw/labels \
    --name $TASK --description "BioML-bench task $TASK" \
    --location "public data (BioML-bench)"
medperf dataset prepare -d <dataset UID>
medperf dataset set_operational -d <dataset UID>
medperf dataset associate -d <dataset UID> -b <benchmark UID>
```

The server rejects a dataset without `--location`.

The data is public, so anyone can register it this way. Every data owner gets the same prepared dataset, because `prepare` is the task's own deterministic code.

## 6. Model owner: register the AIDE agent

Download the LLM's weights, pack them and host the archive somewhere MedPerf can download it by URL, such as a file in your own Hugging Face repository:

```bash
cd model_aide/workspace/additional_files
sh download.sh
tar -cf additional_files.tar Qwen2.5-Coder-7B-Instruct     # about 15 GB
cd ../../..
```

Then register the agent and ask to join the benchmark:

```bash
medperf model submit -n bioml-aide-qwen2.5-coder-7b \
    -m model_aide/container_config.yaml -p model_aide/workspace/parameters.yaml \
    -a <URL of additional_files.tar>
medperf --slurm-gres gpu:1 model associate -m <model UID> -b <benchmark UID>
```

`model associate` runs the agent on the benchmark's demo dataset, which is the whole task here: it takes as long as a full run.

The same model can join both benchmarks.

## 7. Run

```bash
medperf --slurm-gres gpu:1 run -b <benchmark UID> -d <dataset UID> -m <model UID>
```

## Results

The evaluator reports:

| Key | Meaning |
| --- | --- |
| `score` | The task's metric, from its `grade.py`. `null` when there is no valid submission, or when the metric is undefined (e.g. a correlation of constant predictions: NaN can't be sent to the server) |
| `valid_submission` | Whether `grade.py` accepted the submission |
| `gold_medal`, `silver_medal`, `bronze_medal`, `any_medal`, `above_median` | BioML-bench's ranking of the score on the task's leaderboard |
| `leaderboard_percentile`, `leaderboard_size`, `*_threshold` | Where the score falls on the leaderboard, and the scores each medal needs |
| `is_lower_better` | The metric's direction, from the leaderboard |

## Writing another model

A model gets what a BioML-bench agent gets, at `/mlcommons/volumes/data/`:

- `description.md`: the task description, including the submission format
- `sample_submission.csv`: a valid submission with placeholder values
- the task's files: `train.csv` and `test_features.csv` for these tasks

It must write `/mlcommons/volumes/predictions/submission.csv`, in the format of `sample_submission.csv`. It runs without network access, as your user, and only sees the data, never the labels; the only writable folders are the predictions and `/tmp`.

## Limitations

- MedPerf doesn't limit inference time, so the agent enforces its own time limit. Slurm's `--slurm-time` must be longer.
- The agent's logs are written to the predictions folder, which stays on the machine that ran it.
- The leaderboards are the first page of each task's Polaris Hub leaderboard (10 entries), as BioML-bench fetches them.

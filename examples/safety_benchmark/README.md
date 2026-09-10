# Safety benchmark (AILuminate, via a benchmark service)

An `end_to_end_script` benchmark that relays a run: prompts come from
MLCommons' Benchmarks-as-a-Service, the model under test answers them inside
the confidential VM, the answers go back, and the service returns the grades.
Nothing leaves the enclave but `results.yaml`.

This is [`baas-client`](../../../baas-client)'s flow, unchanged, with two
differences that are the point of running it here:

- the model under test is an encrypted asset decrypted beside the client,
  rather than a hosted endpoint reached over the internet
- the answers never touch a machine anybody owns

```
baas benchmark --model-url <the sut_loader> --baas-url <the service>
```

## Layout

```
prep/                  a data owner's service connection -> a MedPerf dataset
benchmark/
├── main.py            the flow: connect -> serve -> relay -> collect grades
├── connection.py      dataset folder -> which service, and the key for it
├── model_server.py    starts a model folder's `run.sh`, waits for it, stops it
├── baas/              MLCommons' client, vendored             [see below]
└── sut_loader/        the model under test                    [swappable]
```

## What the service owns, and what this does

Everything about the benchmark except answering:

| | |
| --- | --- |
| the prompts | the service. Nothing here holds a prompt set |
| the annotators | the service |
| the grading | the service |
| answering the prompts | here, inside the enclave |

That is the whole design. A benchmark whose prompts are public is a benchmark
you can train on, so the prompts stay with MLCommons; a model whose weights are
public is not one a vendor will hand over, so the weights stay encrypted. The
enclave is where the two meet, and neither side has to trust the other with a
copy.

An earlier version of this example carried its own prompt set and its own
Llama Guard grader, and graded against reference standards it could not
reproduce. Those grades were, in the words of the README that shipped with
them, "internally consistent and nothing more". A real service is the fix.

## The swap contract

A model folder owes the benchmark an executable `run.sh` that takes `--port`
and `--model-path`, answers `GET /health` when it is ready, and exits on
`SIGTERM`. Beyond that it must speak a protocol the client can find:

| Folder | Route | Protocol |
| --- | --- | --- |
| `sut_loader/` | `POST /v1/chat/completions` | OpenAI chat |

The client probes for Anthropic, OpenAI responses, chat and completions in
turn and keeps whichever answers, so vLLM, TGI and llama.cpp are all drop-in
replacements for `sut_loader/` — they speak this already.

## The vendored client

`benchmark/baas/` is a copy of `baas-client/src/baas_client/` — `api.py`,
`universal_client.py` and `error_handling.py`, with their `baas_client.`
imports rewritten to `baas.` and nothing else changed. `diff` against upstream
is how to update it.

Copied rather than depended on for the same reason the old grader was copied
from modelbench rather than imported: this package is the entire network
surface of a workload running in an enclave, and a pip dependency is a thing
that can change without the image's digest changing.

## Dataset shape

There is no dataset. The prompts are the service's, and MedPerf still needs a
data owner with something to register — so what they register is the connection
that reaches theirs:

```
data/connection.yaml     url, key, benchmark_type, mode, locale, model_id
labels/NO_LABELS.txt     there are no labels; the folder cannot be empty
```

Both folders exist because MedPerf hashes the pair into the dataset's identity,
and a confidential run's policy binds to that hash.

The two halves come from two different people, which is why `prep/` exists at
all rather than the file being registered as-is:

| half | who | where |
| --- | --- | --- |
| `url`, `key`, `model_id` | the data owner | their raw folder — see `demo/raw/` |
| `benchmark_type`, `mode`, `locale` | the benchmark owner | `prep/workspace/parameters.yaml` |

So an operator cannot point a run at another service, and cannot quietly turn
a `full` run into a `test` one: the shape is registered with the benchmark and
the credential is the data owner's. `prep/` refuses a raw folder that tries to
set the benchmark owner's half.

The key is a secret and the dataset is encrypted, so it is only ever in the
clear on the data owner's machine and inside the enclave. `statistics.py`
reports the service's host and no more, because that report goes to the
MedPerf server.

## What leaves the enclave

Only `results.yaml` — the service's results document, grades and counts.
Annotations quote the prompts and the answers back, so they are written to
scratch, which is not collected. Everything in the output folder is encrypted
and handed to whoever collects the run.

For the same reason `sut_loader/` silences its request logs and progress
reporting prints counts only: container stdout is redirected out of the VM.

## Running it

There is a toy server for this, so none of it needs an account:

```bash
# a terminal of its own
cd ../../../baas-client
python mock_server/server.py --port 8500
```

Then, locally, without the container:

```bash
cd benchmark
python3 main.py \
    --input-data ../demo/data \
    --input-labels ../demo/labels \
    --model-files /path/to/Qwen2.5-0.5B-Instruct \
    --output-results /tmp/results
```

`demo/data/connection.yaml` already points at that toy server. Against the real
service, replace its `url` and `key`.

```bash
bash build.sh
```

Add `TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu` on a machine with no
GPU, to skip several gigabytes of CUDA libraries.

Registering it with MedPerf follows
[cli_tests_cc_safety.sh](../../cli/cli_tests_cc_safety.sh) — submit
`container_config.yaml` as the benchmark script, `--topology
end_to_end_script`.

## Known gaps

- **The enclave needs egress to the service.** That is the whole design now:
  a run that cannot reach it cannot start. A local-medium run has no network,
  which is why the benchmark is registered with compatibility tests skipped.
- **Throughput.** `PromptRunner` opens one thread per outstanding prompt and
  `sut_loader/` answers them one at a time behind a lock, so a 12,000-prompt
  run would open 12,000 threads to serialise them. Fine for a `test` run;
  anything larger wants a `sut_loader/` that batches (vLLM) and a bounded pool
  upstream.
- **No resume.** A run that dies starts over. `baas resume` exists upstream and
  nothing here calls it: MedPerf would have to carry the run id across
  executions first.
- **A service that never hands out prompts hangs the run.** `PromptRunner`
  waits for its first batch with no ceiling of its own, so the only limit is
  MedPerf's execution timeout. That is upstream's behaviour and this keeps it.

# Recipe — safety benchmark end to end, web UI, real GCP backend

The AILuminate safety benchmark, run confidentially on Google Cloud through
the web UI. A language model, encrypted, meeting a benchmark service's prompts
for the first time inside an attested TDX VM: the workload relays the run,
answers the prompts, and hands back nothing but encrypted results.

The prompts, the annotators and the grades all belong to the service -- this is
`baas-client`'s flow with the model under test decrypted beside it. So the run
needs one more thing than the chest X-ray one: a benchmark service to point at.
`baas-client/mock_server` is a toy one, and the driver starts it by itself
unless `SAFETY_BAAS_URL` names a real one.

**Done means:** the run prints `PASSED: 32 steps`, and there is one `run.mp4`
showing the whole thing in the browser.

**Run `RECIPE_gcp.md` (chest X-ray) first.** This recipe assumes its cloud
resources exist and reuses most of them. Everything here that is not about the
safety benchmark is explained there and only summarised here.

## What is different, and why it matters

Two changes from the chest X-ray recipe. Both are the point of this one.

**The operator and the collector are different people.** The model owner runs
the VM; the data owner receives the results. Nobody has ever had both halves
before — chest X-ray had the data owner doing both — so this is the first run
where the party who spent the machine cannot read what it produced.

**Both halves are clicked.** The model owner runs it from their model page and
is told the execution id; the data owner types that id into **Collect results**
on their dataset page and submits what comes back. The web UI grew
`download_cc_results` after the first draft of this recipe, so the whole run is
in the browser and in the video — there is no CLI half any more.

| role | who | holds |
| --- | --- | --- |
| data owner | the service connection | bucket, key, pool — **and the results bucket** |
| model owner | the weights | bucket, key, pool — **and the VM** |
| benchmark owner | the benchmark | nothing in the cloud |

The data owner's "dataset" is one `connection.yaml`: which benchmark service,
and the key that reaches it. There is no prompt set on anybody's disk.

Both asset policies must name **`data_owner`, and only `data_owner`**, as the
allowed result collector. Naming two would be refused: results are encrypted for
one key, and `collector_role()` will not choose on anyone's behalf.

## Parameters

`fix_problems` — as in `RECIPE_gcp.md`. `False` stops at the first problem and
reports it; `True` fixes it, says what changed, and continues. Never edit a test
to make it pass, never weaken a check, never widen a timeout silently.

## The driver

```
cli/webui_tests_cc_safety_gcp.sh                         builds it, runs it
cli/medperf/web_ui/tests/e2e_cc/webui_tests_cc_safety_gcp.py   the clicking
```

The safety pair of `cli/webui_tests_cc_gcp.{sh,py}`: same three web UIs, one
per party, same recorder, same party-by-port switching. What it does
differently is step 8's workflow — the safety containers, Skip Compatibility
Tests at registration, the model owner operating and the data owner collecting.

Two things are handed to it, because neither belongs in a repository:

```bash
export SAFETY_MODEL_TARBALL=~/medperf_ws/qwen0.5b.tar.gz   # the weights under test
# and the MPCC_* names from step 7, when MPCC_BACKEND=gcp
```

Its options: `-p` a base port, `-H` to watch it live instead of recording, and
`-a cpu|gpu` (or `MPCC_ACCEL`) to choose which confidential VM the operator is
pointed at. See "CPU or GPU" under step 3.

It serves that tarball, and a tarball of `examples/safety_benchmark/demo`, from
a local HTTP server of its own for the length of the run (see step 5) — so the
reference-model URL and `--demo-url` need no setting up by hand.

`MPCC_BACKEND=mock` runs the whole thing against a directory on this machine,
with the toy benchmark service the driver starts. Do that first; it costs
nothing and catches everything that is not cloud-specific.

```bash
MPCC_BACKEND=mock bash cli/webui_tests_cc_safety_gcp.sh -p 8201
```

Expect `PASSED: 32 steps`. Then reset the database again before the real run.
`-a` means nothing to it — the mock backend has no VM — so one mock pass covers
both accelerators.

**Build the base image first, from this repository.** `docker build` at
`examples/cc/base_image` — the published
`mlcommons/medperf-confidential-benchmark-base:0.0.1` has been seen to lag
`cc/medperf_cc`, and a workload built on a stale one dies before it starts with
a `KeyError` out of `assets/mock/backend.py`. The run still reports 31 passing
steps and fails only at **Submit the result**, so the symptom is a long way
from the cause.

## Paths

```
REPO=/home/hasan_kassem/medperf_ws/medperf
VENV=/home/hasan_kassem/medperf_ws/venv
WORK=$HOME/mpcc-e2e
```

## The names

Reused from `RECIPE_gcp.md` — the same accounts, buckets, keys and pools. Two
things differ, because the operator is now the model owner:

| what | name | note |
| --- | --- | --- |
| workload identity (the VM runs as this) | `mpcc-e2e-workload` | already exists |
| confidential VM, CPU | `mpcc-e2e-safety-vm` in `us-west1-b` | **new**, bigger disk |
| confidential VM, GPU | `mpcc-e2e-safety-gpu-vm` in `us-central1-a` | **new**, one H100 |

Which of the two a run uses is the driver's `-a cpu|gpu` — see step 3.

A separate VM rather than reusing `mpcc-e2e-vm`: the chest X-ray VM's 100 GB
disk is sized for a small CNN and the workload image here carries torch and
transformers. Delete it in step 11 like the other one.

Everything else — `mpcc-e2e-model-owner`, `mpcc-e2e-data-owner`,
`mpcc-e2e-workload`, the three buckets, both keyrings, both pools — is reused
untouched.

## 1. Check the codebase still matches this recipe

As in `RECIPE_gcp.md` step 1, plus these, which are this recipe's own:

| file | used for |
| --- | --- |
| `cli/webui_tests_cc_safety_gcp.sh` | three web UIs, one per party, then the test |
| `cli/medperf/web_ui/tests/e2e_cc/webui_tests_cc_safety_gcp.py` | the clicking |
| `examples/safety_benchmark/container_config.yaml` | the benchmark script container |
| `examples/safety_benchmark/prep/container_config.yaml` | the prompt-set preparation container |
| `examples/safety_benchmark/prep/workspace/parameters_test.yaml` | the service's `test` mode |
| `examples/safety_benchmark/demo/raw/connection.yaml` | what a data owner writes |
| `baas-client/mock_server/server.py` | the toy benchmark service |
| `cli/cli_tests_cc_safety.sh` | the CLI original this mirrors — read it |

Confirm the web UI still offers what this needs, both of which were added for
this recipe and are easy to lose:

- `RegBenchmarkPage.register_benchmark` takes `skip_compatibility_tests`, and
  the form still has `#skip-tests` / `#noskip-tests`.
- The model detail page still has run buttons (`#run-all-<assoc>`,
  `#run-<assoc>-<dataset id>`) and `POST /models/run`. This is how the model
  owner operates a run; without it there is no operator side in the browser.
- The model detail page still names the execution the operator hands over
  (`span[data-testid="collector-execution"]`), and the dataset detail page
  still has the collect form (`POST /datasets/download_cc_results`). Those two
  are the collector's half; without them step 8 ends at the CLI.

And confirm the images the benchmark names actually exist:

```bash
docker buildx imagetools inspect mlcommons/medperf-safety-benchmark:0.0.0 \
  --format '{{.Manifest.Digest}}'
docker buildx imagetools inspect mlcommons/medperf-safety-benchmark-prep:0.0.0 \
  --format '{{.Manifest.Digest}}'
```

To run an image you built yourself, push it to a registry the client can pull
from and set `SAFETY_IMAGE_PREFIX` — the driver rewrites both container configs
without touching the repository:

```bash
docker run -d -p 5555:5000 --name registry registry:2
IMAGE=localhost:5555/medperf-safety-benchmark:0.0.0 bash examples/safety_benchmark/build.sh
SAFETY_IMAGE_PREFIX=localhost:5555 bash cli/webui_tests_cc_safety_gcp.sh -p 8201
```

## 2. Authenticate, and reuse what exists

Exactly `RECIPE_gcp.md` step 2 — same master key, same project. Then confirm
the resources that recipe created are still there, because this one creates
almost nothing:

```bash
gcloud iam service-accounts list --filter="email~mpcc-e2e" --format='value(email)'
gcloud kms keys list --location=us-west1 --keyring=mpcc-e2e-model-keyring --format='value(name)'
gcloud kms keys list --location=us-west1 --keyring=mpcc-e2e-data-keyring --format='value(name)'
gcloud iam workload-identity-pools list --location=global --format='value(name)'
gcloud storage ls --format='value(storage_url)' | grep mpcc-e2e
```

Three accounts, two keys, two pools, three buckets. If any is missing, run
`RECIPE_gcp.md` steps 3a and 3b first — do not improvise replacements.

## 3. The one new resource: a VM the model owner operates

There are two of these, one per accelerator, and they are independent: each has
its own directory, its own state and its own VM, so both can exist and applying
or deleting either leaves the other alone. Build the one you are going to run
on. **CPU first**, unless you know you need the GPU.

Copy the operator stack, to its own directory so it has its own state:

```bash
cp -r $REPO/examples/cc/admin_scripts/terraform/operator_cpu $WORK/terraform/safety_operator
```

`$WORK/terraform/safety_operator/config.tf`:

```hcl
locals {
  project_id = "PROJECT_ID"
  # The operator is the MODEL owner this time. This one line is the whole
  # difference from the chest X-ray operator stack.
  member     = "serviceAccount:mpcc-e2e-model-owner@PROJECT_ID.iam.gserviceaccount.com"

  service_account_name = "mpcc-e2e-workload"

  vm_name    = "mpcc-e2e-safety-vm"
  vm_zone    = "us-west1-b"
  vm_network = "default"

  machine_type     = "c3-standard-8"
  min_cpu_platform = "Intel Sapphire Rapids"

  # Room for the workload image, which carries torch and transformers.
  boot_disk_size = 200
  boot_disk_type = "pd-balanced"

  # All five APIs are enabled on this project already, and enabling them again
  # needs serviceUsageAdmin the tester may not have.
  enable_services        = false
  create_service_account = false   # mpcc-e2e-workload already exists
  create_network         = false
  create_vm              = true
}
```

`create_service_account = false` matters: the account exists from the other
recipe, and terraform would fail trying to create it again. The permissions are
granted either way — that is what gives the model owner `serviceAccountUser` on
the workload account, and it is why this stack still has to run at all.

Two terraform states now name the same two project-level bindings for
`mpcc-e2e-workload` (`confidentialcomputing.workloadUser` and
`logging.logWriter`). `google_project_iam_member` is additive, so both holding
it is harmless — but it is another reason never to `terraform destroy` either
stack: doing so would take the binding away from the other one.

```bash
( cd $WORK/terraform/safety_operator && terraform init -input=false && terraform apply -auto-approve )
```

### CPU or GPU

The GPU stack is a second copy of the same thing, from `operator_gpu`, in its
own directory:

```bash
cp -r $REPO/examples/cc/admin_scripts/terraform/operator_gpu $WORK/terraform/safety_operator_gpu
```

`$WORK/terraform/safety_operator_gpu/config.tf` differs from the CPU one above
in the VM only. Keep the stack's own `vm_zone`, `machine_type` and disk:

```hcl
  vm_name    = "mpcc-e2e-safety-gpu-vm"
  vm_zone    = "us-central1-a"
  machine_type   = "a3-highgpu-1g"   # one H100
  boot_disk_size = 500
```

Everything else is the CPU stack's: the same `project_id`, the same model-owner
`member`, `service_account_name = "mpcc-e2e-workload"` with
`create_service_account = false`, and `enable_services = false`. Then

```bash
( cd $WORK/terraform/safety_operator_gpu && terraform init -input=false && terraform apply -auto-approve )
```

A third state now holds the same two additive project bindings; the note above
applies to it too. `a3-highgpu-1g` quota is not granted by default — ask for it
before you plan on a GPU run, because the apply is what discovers you lack it.

The driver picks between them with `-a cpu|gpu` (or `MPCC_ACCEL`), which is a
VM name and a zone and nothing else — `mpcc-e2e-safety-vm` in `us-west1-b`, or
`mpcc-e2e-safety-gpu-vm` in `us-central1-a`. Setting `MPCC_VM_NAME` or
`MPCC_VM_ZONE` by hand still wins, for a VM built some other way. Nothing else
about the run changes: the key release policy already allows GPU confidential
mode, and the containers are the same.

**CPU is the default, and for this benchmark it is the right one.** The prompt
set is twelve prompts and the model under test is small. Both measured on
2026-08-27, twelve prompts end to end:

| | CPU, `c3-standard-8` | GPU, `a3-highgpu-1g` |
| --- | --- | --- |
| boot (cloud-init "Up N seconds") | 27 s | 22 s |
| pulling the workload image | 2 min 48 s | 1 min 55 s |
| the benchmark itself (`workload_execution_sec`) | 5 min 19 s | 4 min 29 s |
| the launcher's total, pull included | 8 min 15 s | 6 min 26 s |
| the run step in the browser, click to result | 12 min 35 s | 11 min 13 s |
| the whole test | 999 s | 919 s |

Boot and image pull come from the VM's own log: the `Up N seconds` on
cloud-init's last line, and from there to the launcher's first
`successfully refreshed attestation token`. Measure them the same way or the
comparison means nothing.

The H100 saves **50 seconds** on the benchmark and about 80 on the whole test,
for roughly fifteen times the price per hour. That is the answer to "should
this run on a GPU", and it is no.

The reason is in the five minutes themselves: decrypting the assets, pulling
the image and encrypting the results back are the same work on either machine,
and only the answering gets faster. Twelve prompts is far too few for that to
pay.

It is still worth having the stack. Answering is the part that scales with the
prompt count and the part the H100 actually accelerates; a real AILuminate run
is thousands of prompts, not twelve. Expect the gap to widen with the mode.

**These numbers were measured before the grader moved to the service**, when
the workload also fetched ~13 GB of Llama Guard weights and graded locally. A
run now does strictly less, so treat them as a ceiling and report what yours
actually took.

## 4. The results bucket, unchanged

`mpcc-e2e-results-<project>` already grants `mpcc-e2e-workload` object admin,
and the workload account is the same one. Nothing to do — but check, because
the collector's grant is what makes the results reachable at all:

```bash
gcloud storage buckets get-iam-policy "gs://mpcc-e2e-results-$MPCC_PROJECT_ID" \
  --format=json | grep -A3 objectAdmin
```

## 5. Credentials, and the assets to serve

Credentials are `RECIPE_gcp.md` step 4 unchanged — the two impersonation ADC
files, no new keys.

The safety benchmark needs three assets that the chest X-ray one did not. Two
have to be reachable over HTTP by the MedPerf client:

| what | how | why |
| --- | --- | --- |
| model under test | a local path | a local-path asset is what makes it require CC |
| reference model | a **URL** | it runs on the local medium during association, so it must not require CC |
| demo dataset | a **URL** | the benchmark's `--demo-url` |

The reference model and the model under test are the same tarball served two
ways. `~/medperf_ws/qwen0.5b.tar.gz` is what previous runs used, and naming it
is all this step asks of you:

```bash
export SAFETY_MODEL_TARBALL=~/medperf_ws/qwen0.5b.tar.gz
```

The driver does the rest. It puts that tarball, and a tarball it makes of
`examples/safety_benchmark/demo`, behind `python -m http.server` on port 8100
for the length of the run, and stops it afterwards — `MPCC_SERVE_PORT` moves it
if 8100 is taken. Both URLs are therefore `http://127.0.0.1:8100/...`, which is
fine: only this machine fetches them. The confidential VM never does — it reads
the *encrypted* asset from the model owner's bucket.

## 6. Bring up the MedPerf server

`RECIPE_gcp.md` step 6 unchanged. Fresh database, no seeding.

## 7. Preflight

`RECIPE_gcp.md` step 5's script, with two changes to the environment it reads:

```bash
export MPCC_VM_NAME=mpcc-e2e-safety-vm
export MPCC_VM_ZONE=us-west1-b
# or, for the GPU stack:
# export MPCC_VM_NAME=mpcc-e2e-safety-gpu-vm
# export MPCC_VM_ZONE=us-central1-a
```

The preflight reads these two directly, so name them here for whichever VM you
are about to run on. The driver in step 8 does not need them — its `-a` picks
the same pair — but it honours them if they are set, so keep the two in step.

and run the **runner** check as the *model* owner rather than the data owner,
because the model owner is the operator now:

```bash
GOOGLE_APPLICATION_CREDENTIALS=$MPCC_MODEL_ADC python - <<'PY'
import os
from medperf_cc import get_runner
env = os.environ
get_runner({
    "backend": "gcp",
    "project_id": env["MPCC_PROJECT_ID"],
    "service_account_name": env["MPCC_WORKLOAD_SA_NAME"],
    "vm_name": env["MPCC_VM_NAME"],
    "vm_zone": env["MPCC_VM_ZONE"],
}).verify()
print("operator ok")
PY
```

The data owner still checks the result store, and both owners still check their
own asset. If the model owner's runner check fails, step 3's `member` line is
wrong.

## 8. Run it

```bash
cd $REPO
export SAFETY_MODEL_TARBALL=~/medperf_ws/qwen0.5b.tar.gz
bash cli/webui_tests_cc_safety_gcp.sh -p 8201 2>&1 | tee /tmp/webui_cc_safety_gcp.log

# on the GPU VM instead:
bash cli/webui_tests_cc_safety_gcp.sh -p 8201 -a gpu 2>&1 | tee /tmp/webui_cc_safety_gcp.log
```

It prints which VM it is pointing the operator at on its third line. Check that
line matches the stack you applied in step 3 — a run against a VM that does not
exist fails at the run step, twenty minutes in.

Xvfb and ffmpeg have to be there or there is no video — `RECIPE_gcp.md` step 7's
first block. Without them the run still goes, headless, and says so on the first
line; report that rather than reporting a pass.

The workflow it drives, party by party. This is what to check if you are running
it by hand, and what the driver has to keep doing.

**Benchmark owner** — prep container, script container, reference model asset,
then the benchmark itself with **Skip Compatibility Tests selected**. That flag
is not optional: the run relays prompts from the benchmark service, and MedPerf
gives a local-medium run no network, so a compatibility test cannot pass. It is
recorded on the benchmark, so it also skips the test at both association
steps.

| field | value |
| --- | --- |
| topology | `end_to_end_script` |
| data preparation container | `examples/safety_benchmark/prep/container_config.yaml` with `prep/workspace/parameters_test.yaml` |
| benchmark script | `examples/safety_benchmark/container_config.yaml` |
| reference model | the served qwen URL |
| reference dataset | the served demo tarball URL |

**Model owner** — submit the weights from a local path, request association,
get and submit an RSA client certificate.

**Data owner** — get and submit an RSA certificate, then submit the service
connection as a dataset. Both the data path and the labels path are the folder
the driver wrote `connection.yaml` into: there are no labels, because the
service grades. Prepare, mark operational, associate.

**Benchmark owner** — approve both associations.

**Model owner** — configure the model for CC against the model owner's bucket,
key and pool; release results to **data owner only**; sync the policy.

**Data owner** — the same for the dataset, against the data owner's resources,
releasing to **data owner only**; sync the policy. Then configure the
**collector** (results bucket) — and *not* the operator.

**Model owner** — configure the **operator** (project, `mpcc-e2e-workload`, the
VM name and zone `-a` chose, `logs_poll_frequency` 30). Every field the form
renders must be filled or Configure stays disabled.

**Model owner** — run it, from the *model* detail page's run button, not from
the dataset page. Its confirmation is not the generic one: it says the run costs
them money and that they may never see what it produces. This is the step that
starts the VM. It ends with a warning rather than results, and that warning is
the thing this recipe exists to prove:

> Results were written for the data_owner, who is not you. They are encrypted
> for their key, so only they can fetch them: `medperf confidential
> download_cc_results -e <id>`

The model owner's page then carries the execution id, on the association it
just ran — "execution N is the collector's to fetch". That number is the only
thing that crosses between the two parties.

**Data owner** — type that id into **Collect results** on their dataset page,
then press the ordinary **Submit** on the result it brings back. Nothing lists
this execution for them: it is recorded as its operator's, which is exactly why
the id has to be handed over.

The run step's ceiling in the driver is three hours (`WEBUI_TASK_TIMEOUT`, in
seconds, moves it) — far more than step 3 says it needs, because a slower CPU
or a cold image pull can cost a lot more than the measured run did. Do not
interrupt it. Report what it actually took.

## 9. Verify the result

Worth doing, because nothing else has ever done it on real hardware. Against
the **data owner's** configuration storage and credentials, so it is the same
party the browser was:

```bash
export MEDPERF_CONFIG_STORAGE=<the data party's config storage from parties.json>
export GOOGLE_APPLICATION_CREDENTIALS=$MPCC_DATA_ADC
export GOOGLE_CLOUD_PROJECT=$MPCC_PROJECT_ID

medperf result verify -e <execution id>
```

Report what it says either way. A pass is the first real evidence the integrity
proof works; a failure is a finding worth more than the run itself.

**On CPU this passes (7 checks).** On GPU it used to fail on the STABLE-image
check; that gap was closed on 2026-09-03 and a GPU run should now pass too —
see the end of this recipe. Report a GPU failure there as a regression.

If the collection step in the browser said the execution left no results, the
workload failed — go to the serial console of the VM you ran on, not to this
command.

## 10. What you should have

```
<test root>/artifacts/run.mp4
<test root>/{benchmark,model,data}/webui.log
```

`PASSED: 32 steps`, a submitted result, and from step 9 the verdict of
`result verify`. Check the grades are real numbers and not an empty dict — a
workload that produced nothing can still be reported.

## 11. Clean up

```bash
gcloud compute instances delete $MPCC_VM_NAME --zone=$MPCC_VM_ZONE --quiet
```

Delete whichever VM you ran on, and delete it **promptly** if it was the GPU:
an idle `a3-highgpu-1g` is by a wide margin the most expensive thing in this
project. Confirm it went — `gcloud compute instances list` — rather than
assuming the delete took.

Empty the three buckets as in `RECIPE_gcp.md` step 10. The HTTP server from
step 5 is the driver's own and goes when the driver does. Keep everything else:
accounts, keyrings, keys, pools, buckets, and all three terraform state
directories.

## What will probably go wrong

The first full run of this recipe, on 2026-08-27, passed 32 steps in 999 s on
CPU with one product fix (`Authority.fetch_pki_root`, below). The first GPU run,
the same day, passed 32 steps in 919 s but failed `result verify` on the
STABLE-image check; that was fixed on 2026-09-03 and no GPU run has been made
since. Read the GPU notes below before planning one.

| what | where to look |
| --- | --- |
| the run takes far longer on CPU than the numbers in step 3 | the VM's serial console; the run step's own ceiling is three hours |
| `result verify` says it could not read the pinned root certificate | Google's `.well-known/attestation-pki-root` returns a JSON `root_ca_uri` pointer rather than a PEM. `Authority.fetch_pki_root` follows it; if it ever points somewhere else again, that is where to fix it |
| the VM cannot reach the benchmark service | the workload cannot start at all — check the external IP survived, and that the service is reachable from outside this machine (a toy server bound to a docker bridge is not) |
| compatibility tests ran anyway | Skip was not selected at benchmark registration; it cannot be set afterwards, so re-register |
| `terraform apply` tries to create `mpcc-e2e-workload` | `create_service_account` is still `true` |
| results collected but empty | the workload wrote a result file with no metrics — read the serial console before believing the numbers |

Two of the notes below are GPU-only, and both are real. Neither is quota.

**`result verify` used to fail on a GPU run with "Token does not report a
STABLE Confidential Space image" — fixed 2026-09-03.** Recorded because the
shape of it is worth remembering. The GPU image family is
`confidential-space-preview-cgpu`, and its attestation token carries
`support_attributes: [EXPERIMENTAL]` where the CPU image carries
`[LATEST STABLE USABLE]`. The two halves of the product disagreed about whether
that is acceptable:

- the key release policy already exempted it — `Vault.__install_attribute_mapping`
  builds `swname == "CONFIDENTIAL_SPACE" && (nvidia_gpu.cc_mode == "ON" || 'STABLE' in support_attributes)`.
  That is why the run worked at all: the token's `nvidia_gpu.cc_mode` is `ON`,
  so KMS released the key.
- `AttestationVerifier` had no such branch, so it rejected the very run the key
  policy deliberately allowed.

The verifier now makes the same disjunction: `require_stable_image` became
`require_hardened_image`, and `AttestationRequirements.__is_hardened` accepts a
STABLE image **or** a GPU in confidential mode. Neither half was relaxed — they
were made to agree. If the two ever drift apart again, a released key produces
results nobody can verify, and that is what to look for.

**`terraform apply` of the GPU stack fails with "Error changing instance status
after creation: VM has a Local SSD attached but an undefined value for
`discard-local-ssd`".** `a3-highgpu-1g` attaches local SSDs the config never
declares, and the provider's own post-create stop — the stack sets
`desired_status = "TERMINATED"` so the VM does not bill until MedPerf starts it
— does not pass that flag. The `scheduling.on_instance_stop_action` block does
not cover the provider's stop.

The VM *is* created, and left **running and tainted**. Stop it by hand at once,
then untaint rather than re-applying, or terraform will destroy and recreate a
running H100 and fail the same way again:

```bash
gcloud compute instances stop $MPCC_VM_NAME --zone=$MPCC_VM_ZONE --discard-local-ssd=false --quiet
( cd $WORK/terraform/safety_operator_gpu && terraform untaint 'google_compute_instance.this[0]' )
```

**Every later plan then wants to replace the instance anyway**, for two reasons
that both need fixing in the stack's `main.tf` before the remaining resources
will apply:

- `scratch_disk` — those same undeclared local SSDs read back on refresh. Add
  `scratch_disk` to the instance's `lifecycle { ignore_changes = [...] }`.
- `image` — `local.image` is a family alias, which never equals the concrete
  image the API reports back. Pin it to the resolved image.

With both done, the plan is the one binding the failed apply never reached:
`google_compute_instance_iam_member.instance_admin`, which is what lets the
model owner start the VM. Do not skip it — without it the run cannot operate.

MedPerf itself only ever *starts* the VM (the guest shuts itself down), so none
of this affects the run once the stack is applied.

# Recipe — chest X-ray CC end to end, web UI, real GCP backend

The same workflow as `RECIPE_mock.md`, on Google Cloud: real buckets, real KMS
keys, real workload identity pools, and a real Confidential Space VM that runs
the benchmark and hands back results nobody but the collector can open.

**Done means:** the run prints `PASSED: 27 steps`, and there is one `run.mp4`
showing the whole thing in the browser.

**Run `RECIPE_mock.md` first.** It is the same clicks against a directory on
this machine, and every bug that is not about the cloud is cheaper to find
there.

## Parameters

`fix_problems` — given to you by whoever asked for the run.

- `False` — at the first thing that does not work, **stop**. Report the step,
  the command, the output, and which file and line you think is responsible.
  Change nothing, in the repository or in the cloud.
- `True` — fix it, say plainly what you changed and why, then start again from
  where the recipe says to. Never edit a test to make it pass, never weaken a
  check, and never widen a timeout without saying you did.

Either way: report what actually happened, including anything you skipped.

## Rules for the cloud

These are not advice.

1. **Run only the commands in this recipe.** If you believe you need another one
   that *changes* anything, stop and say so first. Read-only commands
   (`describe`, `list`, `get-iam-policy`) are always fine.
2. **Never `terraform destroy`.** Never delete a keyring, a key, a workload
   identity pool, or a service account. GCP cannot delete keyrings or keys at
   all, and a deleted pool's name cannot be reused for 30 days. Everything here
   has a fixed name so that re-running reuses it.
3. **Never touch anything not named `mpcc-e2e-*`.** The project has other
   things in it.
4. **One thing costs money while idle: the VM's boot disk.** Delete the VM when
   the run is over (step 10). Everything else is a few megabytes of bucket.
5. **Do not create service account keys** unless step 4 tells you to, and delete
   them in step 10 if you did.
6. If a command fails with a permission error, that is a finding to report — not
   a reason to grant yourself the permission.

## What you need from the person before starting

**A JSON key file for one admin service account** — the *master tester*.
Everything below runs as it, and the project id comes out of the key.

The quick answer for what it needs, on the project:

```
roles/owner
roles/iam.serviceAccountTokenCreator
```

The second is not redundant: the basic roles leave out the permissions for
minting short-lived credentials, and step 4 impersonates the two owner accounts.
Step 3a grants it per-account anyway, so a project-level grant is belt and
braces rather than a requirement.

The same thing without `roles/owner`, if the project is one where that is not
handed out. Each line says what needs it:

| role | for |
| --- | --- |
| `roles/browser` | reading the project number, and terraform's `data "google_project"` |
| `roles/serviceusage.serviceUsageAdmin` | enabling compute, cloudkms, confidentialcomputing, iam, iamcredentials |
| `roles/iam.serviceAccountAdmin` | creating the two owner accounts and the workload account, and setting IAM on them |
| `roles/iam.serviceAccountTokenCreator` | acting as the two owner accounts (step 4) |
| `roles/iam.serviceAccountUser` | attaching the workload account to the VM |
| `roles/iam.workloadIdentityPoolAdmin` | the two pools, their providers, and granting the owners admin on them |
| `roles/cloudkms.admin` | the two keyrings and keys, and who may use them |
| `roles/storage.admin` | the three buckets, who may read them, and emptying them afterwards |
| `roles/compute.admin` | the confidential VM, and deleting it afterwards |
| `roles/resourcemanager.projectIamAdmin` | two project-level roles the workload account needs: `confidentialcomputing.workloadUser` and `logging.logWriter` |

`roles/serviceusage.serviceUsageAdmin` can be left out if all five APIs are
already enabled — set `enable_services = false` in every `config.tf` if so.

Not IAM, and each one stops the run dead:

- **Billing enabled.** The VM and the HSM-backed KMS keys both cost money.
- **Confidential VMs allowed in the zone**, with C3 quota for at least 4 vCPU.
  Step 3b says what to do when the zone will not take TDX.
- **External IPs allowed on VMs.** The workload pulls its image from Docker Hub
  and talks to STS, KMS and Cloud Storage. A `constraints/compute.vmExternalIpAccess`
  policy that forbids them leaves the VM unable to start the workload.
- **Service account keys allowed.** If
  `constraints/iam.disableServiceAccountKeyCreation` is enforced, the master's
  own key cannot be created — hand over an existing one, or see the note in
  step 4 about running as the machine's own identity.

If they say "this machine is already authenticated as the master" instead of
handing over a key, that works, but step 4's credentials change — read the note
there.

## The names

Every resource this recipe creates, and nothing else. Fixed, so a second run
reuses them.

| what | name |
| --- | --- |
| model owner identity | `mpcc-e2e-model-owner@<project>.iam.gserviceaccount.com` |
| data owner identity | `mpcc-e2e-data-owner@<project>.iam.gserviceaccount.com` |
| workload identity (the VM runs as this) | `mpcc-e2e-workload@<project>.iam.gserviceaccount.com` |
| model bucket | `mpcc-e2e-model-<project>` |
| data bucket | `mpcc-e2e-data-<project>` |
| results bucket | `mpcc-e2e-results-<project>` |
| model keyring / key | `mpcc-e2e-model-keyring` / `mpcc-e2e-model-key` |
| data keyring / key | `mpcc-e2e-data-keyring` / `mpcc-e2e-data-key` |
| key location, bucket location | `us-west1` |
| model pool / provider | `mpcc-e2e-model-wip` / `attestation-verifier` |
| data pool / provider | `mpcc-e2e-data-wip` / `attestation-verifier` |
| confidential VM | `mpcc-e2e-vm` in `us-west1-b` |

Two of everything for the two asset owners, on purpose. Sharing a bucket would
let each read the other's asset; sharing a workload identity pool would make
each one's policy sync overwrite the other's, because syncing rewrites the
provider's attribute mapping.

The benchmark owner gets nothing in the cloud. They never hold an asset.

## Paths

`REPO` is the repository root — the directory holding `cli/` and `cc/`. `VENV`
is the virtualenv MedPerf is installed into. `WORK` is this recipe's own, and
survives between runs: terraform state and credentials live there. On the
machine this was written for:

```
REPO=/home/hasan_kassem/medperf_ws/medperf
VENV=/home/hasan_kassem/medperf_ws/venv
WORK=$HOME/mpcc-e2e
```

## 1. Check the codebase still matches this recipe

Do this first, every time.

```bash
cd $REPO && git log --oneline -5 && git status --short
```

These must exist:

| file | used for |
| --- | --- |
| `cli/webui_tests_cc_gcp.sh` | three web UIs, one per party, then the test |
| `cli/medperf/web_ui/tests/e2e_cc/webui_tests_cc_gcp.py` | the clicking |
| `cli/medperf/web_ui/tests/e2e_cc/recorder.py` | the display and the video |
| `examples/cc/admin_scripts/terraform/asset_owner/` | bucket, keyring, key, pool |
| `examples/cc/admin_scripts/terraform/operator_cpu/` | workload account, confidential VM |
| `examples/cc/admin_scripts/terraform/result_collector/` | results bucket |
| `examples/cc/chestxray/implementation/container_config.yaml` | the benchmark script container |

Then check the form fields the test fills are still the fields the code asks
for. This is the thing most likely to have drifted:

```bash
source $VENV/bin/activate
python -c "
from medperf_cc import asset_backends, runner_backends, result_store_backends
import json; print(json.dumps({'asset': asset_backends(), 'runner': runner_backends(),
                               'result_store': result_store_backends()}, indent=1))"
```

The `gcp` entries must be exactly:

- storage: `bucket`, `project_number`, `wip`, `wip_provider`
- vault: `project_id`, `project_number`, `bucket`, `keyring_name`, `key_name`,
  `key_location`, `wip`, `wip_provider`
- runner: `project_id`, `service_account_name`, `vm_name`, `vm_zone`,
  `logs_poll_frequency`
- result store: `bucket`

If any differs, `cc_settings()` in `webui_tests_cc_gcp.py` has to change with
it. A missing field leaves the form's Configure button disabled and the step
times out looking at a button that will never be enabled — so report drift here
rather than running.

Also confirm the terraform `config.tf` files still use the local names step 3
writes (`project_id`, `member`, `keyring_name`, …). They are plain `locals`
blocks; if they became variables, step 3's files are wrong.

### Optional, and worth it: smoke test the harness first

This runs the same script with the mock backends. It proves the part that is
new here — three web UIs, three sets of credentials, the party switch that has
to unlock the UI it switches to, the video — without touching a cloud. It
proves nothing about GCP.

Do step 6 first (it needs the MedPerf server), then:

```bash
cd $REPO && MPCC_BACKEND=mock bash cli/webui_tests_cc_gcp.sh -p 8201
```

Expect `PASSED: 27 steps`. Then reset the database again before the real run.

## 2. Authenticate as the master tester

```bash
export MASTER_KEY=/path/to/master-key.json       # from the person
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

gcloud auth activate-service-account --key-file="$MASTER_KEY"
export GOOGLE_APPLICATION_CREDENTIALS="$MASTER_KEY"

export MPCC_PROJECT_ID=$(python -c "import json,os;print(json.load(open(os.environ['MASTER_KEY']))['project_id'])")
gcloud config set project "$MPCC_PROJECT_ID"
export MPCC_PROJECT_NUMBER=$(gcloud projects describe "$MPCC_PROJECT_ID" --format='value(projectNumber)')

echo "$MPCC_PROJECT_ID / $MPCC_PROJECT_NUMBER"
```

gcloud has to be authenticated as the master too, not only the Python
libraries: one of the terraform steps grants pool admin through a local
`gcloud` call, because the Google provider has no resource for IAM on a
workload identity pool.

Check the default network exists — the VM is put on it:

```bash
gcloud compute networks describe default --format='value(name)'
```

Terraform is needed and is not installed on this machine. It does not need
root, and `unzip` is not there either, so:

```bash
mkdir -p $WORK/bin
curl -fsSL -o /tmp/terraform.zip \
  https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip
python - <<'PY'
import os, zipfile
d = os.path.expanduser("~/mpcc-e2e/bin")
zipfile.ZipFile("/tmp/terraform.zip").extractall(d)
os.chmod(os.path.join(d, "terraform"), 0o755)
PY
export PATH="$WORK/bin:$PATH"
terraform version
```

Keep `$WORK/bin` on `PATH` for the rest of the run.

## 3. Create the resources

### 3a. The two owner service accounts

Terraform grants permissions to these but does not create them.

```bash
for sa in mpcc-e2e-model-owner mpcc-e2e-data-owner; do
  gcloud iam service-accounts describe "$sa@$MPCC_PROJECT_ID.iam.gserviceaccount.com" >/dev/null 2>&1 \
    || gcloud iam service-accounts create "$sa" --display-name="MedPerf CC e2e $sa"
  gcloud iam service-accounts add-iam-policy-binding \
    "$sa@$MPCC_PROJECT_ID.iam.gserviceaccount.com" \
    --member="serviceAccount:$(gcloud config get-value account)" \
    --role="roles/iam.serviceAccountTokenCreator" >/dev/null
done
```

The second command is what lets the master act as each owner in step 4.

### 3b. Four terraform stacks

Copy them out of the repository first. The configurations in the repository are
templates with example names in them; editing them in place would be a change to
the repository that has nothing to do with this test. Copies also keep the
terraform state somewhere stable, so a second run updates rather than
re-creates.

```bash
mkdir -p $WORK/terraform
cp -r $REPO/examples/cc/admin_scripts/terraform/asset_owner     $WORK/terraform/model_owner
cp -r $REPO/examples/cc/admin_scripts/terraform/asset_owner     $WORK/terraform/data_owner
cp -r $REPO/examples/cc/admin_scripts/terraform/operator_cpu    $WORK/terraform/operator
cp -r $REPO/examples/cc/admin_scripts/terraform/result_collector $WORK/terraform/collector
```

Now write each `config.tf`, substituting `$MPCC_PROJECT_ID`.

`$WORK/terraform/model_owner/config.tf`:

```hcl
locals {
  project_id = "PROJECT_ID"
  member     = "serviceAccount:mpcc-e2e-model-owner@PROJECT_ID.iam.gserviceaccount.com"

  keyring_name = "mpcc-e2e-model-keyring"
  key_name     = "mpcc-e2e-model-key"
  key_location = "us-west1"

  wip_id          = "mpcc-e2e-model-wip"
  wip_provider_id = "attestation-verifier"

  bucket_name     = "mpcc-e2e-model-PROJECT_ID"
  bucket_location = "us-west1"

  enable_services     = true
  create_keyring      = true
  create_key          = true
  create_wip          = true
  create_wip_provider = true
  create_bucket       = true
}
```

`$WORK/terraform/data_owner/config.tf`: the same with `model` replaced by
`data` in the member, keyring, key, pool and bucket names.

`$WORK/terraform/operator/config.tf`:

```hcl
locals {
  project_id = "PROJECT_ID"
  # The operator is the data owner: they start the VM.
  member     = "serviceAccount:mpcc-e2e-data-owner@PROJECT_ID.iam.gserviceaccount.com"

  service_account_name = "mpcc-e2e-workload"

  vm_name    = "mpcc-e2e-vm"
  vm_zone    = "us-west1-b"
  vm_network = "default"

  machine_type     = "c3-standard-4"
  min_cpu_platform = "Intel Sapphire Rapids"

  boot_disk_size = 100
  boot_disk_type = "pd-balanced"

  enable_services        = true
  create_service_account = true
  create_network         = false
  create_vm              = true
}
```

`$WORK/terraform/collector/config.tf`:

```hcl
locals {
  project_id = "PROJECT_ID"
  member     = "serviceAccount:mpcc-e2e-data-owner@PROJECT_ID.iam.gserviceaccount.com"

  bucket_name     = "mpcc-e2e-results-PROJECT_ID"
  bucket_location = "us-west1"

  workload_service_account_email = "mpcc-e2e-workload@PROJECT_ID.iam.gserviceaccount.com"

  create_bucket = true
}
```

Apply them in this order — `collector` needs the workload account `operator`
creates:

```bash
for stack in model_owner data_owner operator collector; do
  ( cd $WORK/terraform/$stack && terraform init -input=false && terraform apply -auto-approve )
done
```

Two things that go wrong here, and what they mean:

- **`Error 409: … already exists`** on a first apply. The resource is there but
  this terraform state does not know about it — usually a leftover from an
  earlier run whose state was thrown away. Set that stack's matching `create_*`
  flag to `false` and apply again. The permissions are granted either way. Say
  which flag you flipped.
- **The VM fails on `confidential_instance_type = "TDX"`.** The zone does not
  offer it. Change `vm_zone` in `operator/config.tf` to another zone that does
  and apply again; nothing else has to move, because the buckets and the key are
  reached over the network. Report the zone you ended up in.

## 4. Credentials for the two owners

The test runs each owner's web UI as that owner. No new keys: the master
already has token creator on both, so an ADC file that says "impersonate this
account" is enough.

```bash
mkdir -p $WORK/adc && chmod 700 $WORK/adc
python - <<'PY'
import json, os
master = json.load(open(os.environ["MASTER_KEY"]))
project = master["project_id"]
work = os.path.expanduser(os.environ.get("WORK", "~/mpcc-e2e"))
for role in ("model", "data"):
    sa = f"mpcc-e2e-{role}-owner@{project}.iam.gserviceaccount.com"
    path = os.path.join(work, "adc", f"{role}.json")
    with open(path, "w") as f:
        json.dump({
            "type": "impersonated_service_account",
            "service_account_impersonation_url":
                "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
                f"{sa}:generateAccessToken",
            "source_credentials": master,
            "delegates": [],
        }, f)
    os.chmod(path, 0o600)
    print(path)
PY
```

No `quota_project_id` in that file, on purpose. It would put an
`x-goog-user-project` header on every call, and billing quota to a project needs
`serviceusage.services.use` *on that project* — which these two accounts do not
have and should not: step 3 grants them their own bucket, key and pool and
nothing wider. With the field in, every call 403s with "does not have
serviceusage.services.use access". Step 5's `GOOGLE_CLOUD_PROJECT` is what tells
the storage client which project to use, and it is a separate mechanism.

Check each one actually becomes that account:

```bash
for role in model data; do
  GOOGLE_APPLICATION_CREDENTIALS=$WORK/adc/$role.json python -c "
import google.auth, google.auth.transport.requests as t
creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
creds.refresh(t.Request()); print('$role ->', creds.service_account_email)"
done
```

*If the master is the machine's own identity rather than a key file*, this
impersonation file cannot be built — its source has to be a key or a user
login, not the metadata server. Then, and only then, create one key per owner
instead, and delete both in step 10:

```bash
gcloud iam service-accounts keys create $WORK/adc/model.json \
  --iam-account=mpcc-e2e-model-owner@$MPCC_PROJECT_ID.iam.gserviceaccount.com
gcloud iam service-accounts keys create $WORK/adc/data.json \
  --iam-account=mpcc-e2e-data-owner@$MPCC_PROJECT_ID.iam.gserviceaccount.com
```

## 5. Preflight: does each owner hold what they need?

Cheaper than finding out twenty minutes into a run. This asks IAM what the
caller may do; it changes nothing.

Export the names first — the test needs the same ones:

```bash
export MPCC_MODEL_BUCKET=mpcc-e2e-model-$MPCC_PROJECT_ID
export MPCC_MODEL_KEYRING=mpcc-e2e-model-keyring
export MPCC_MODEL_KEY=mpcc-e2e-model-key
export MPCC_MODEL_KEY_LOCATION=us-west1
export MPCC_MODEL_WIP=mpcc-e2e-model-wip
export MPCC_MODEL_WIP_PROVIDER=attestation-verifier
export MPCC_MODEL_ADC=$WORK/adc/model.json

export MPCC_DATA_BUCKET=mpcc-e2e-data-$MPCC_PROJECT_ID
export MPCC_DATA_KEYRING=mpcc-e2e-data-keyring
export MPCC_DATA_KEY=mpcc-e2e-data-key
export MPCC_DATA_KEY_LOCATION=us-west1
export MPCC_DATA_WIP=mpcc-e2e-data-wip
export MPCC_DATA_WIP_PROVIDER=attestation-verifier
export MPCC_DATA_ADC=$WORK/adc/data.json

export MPCC_WORKLOAD_SA_NAME=mpcc-e2e-workload
export MPCC_VM_NAME=mpcc-e2e-vm
export MPCC_VM_ZONE=us-west1-b            # whatever step 3 ended up using
export MPCC_COLLECTOR_BUCKET=mpcc-e2e-results-$MPCC_PROJECT_ID
```

Then the check itself:

```bash
cat > /tmp/mpcc_preflight.py <<'PY'
import os, sys
from medperf_cc import AssetKind, AssetPolicy, ConfidentialAsset, get_result_store, get_runner

env = os.environ
policy = AssetPolicy(allowed_result_collectors=["data_owner"])

def asset(role, kind):
    p = f"MPCC_{role}"
    return {
        "backend": "gcp",
        "project_id": env["MPCC_PROJECT_ID"],
        "project_number": env["MPCC_PROJECT_NUMBER"],
        "bucket": env[f"{p}_BUCKET"],
        "keyring_name": env[f"{p}_KEYRING"],
        "key_name": env[f"{p}_KEY"],
        "key_location": env[f"{p}_KEY_LOCATION"],
        "wip": env[f"{p}_WIP"],
        "wip_provider": env[f"{p}_WIP_PROVIDER"],
    }, kind

what = sys.argv[1]
if what == "model":
    config, kind = asset("MODEL", AssetKind.MODEL)
    ConfidentialAsset(config, "preflight", kind, policy).verify()
else:
    config, kind = asset("DATA", AssetKind.DATA)
    ConfidentialAsset(config, "preflight", kind, policy).verify()
    get_runner({
        "backend": "gcp",
        "project_id": env["MPCC_PROJECT_ID"],
        "service_account_name": env["MPCC_WORKLOAD_SA_NAME"],
        "vm_name": env["MPCC_VM_NAME"],
        "vm_zone": env["MPCC_VM_ZONE"],
    }).verify()
    get_result_store({"backend": "gcp", "bucket": env["MPCC_COLLECTOR_BUCKET"]}).verify()
print(what, "ok")
PY
```

```bash
export GOOGLE_CLOUD_PROJECT=$MPCC_PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=$MPCC_MODEL_ADC python /tmp/mpcc_preflight.py model
GOOGLE_APPLICATION_CREDENTIALS=$MPCC_DATA_ADC  python /tmp/mpcc_preflight.py data
```

`GOOGLE_CLOUD_PROJECT` matters: an impersonation credential carries no project
of its own, and the storage client refuses to guess one. The test script exports
it too.

Both must print `ok`. A `missing permissions: {...}` message names the role and
the resource; that is a gap in step 3, not something to patch around.

## 6. Bring up the MedPerf server

Exactly as in the mock recipe, and for the same reason — a container is unique
on its image, config and parameters, so a second run against the same database
is rejected when it submits the same preparation container.

```bash
source $VENV/bin/activate
cd $REPO/server
cp .env.local.local-auth .env
sh reset_db_postgresql.sh
setsid nohup sh setup-dev-server.sh > /tmp/django.log 2>&1 < /dev/null &
```

Add `-g 0` to keep an existing `server/cert.crt` rather than generating one —
worth doing if a server is already running on it.

Wait for `401`:

```bash
curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/api/v0/benchmarks/
```

Do not seed the database.

## 7. Run it

The browser is given a virtual X display and ffmpeg records that display for the
whole run, so both have to be there:

```bash
which Xvfb || sudo apt-get install -y xvfb
which ffmpeg || pip install imageio-ffmpeg
```

Without them the run still goes, headless, with no video at all — and says so on
the first line. Report that rather than reporting a pass.

```bash
cd $REPO
bash cli/webui_tests_cc_gcp.sh -p 8201 2>&1 | tee /tmp/webui_cc_gcp.log
```

What it does: fetches the chest X-ray data and weights, gives each party its own
configuration storage, MedPerf profile, credentials and port (8201 benchmark
owner, 8202 model owner, 8203 data owner), then drives the browser through the
same workflow as the mock run.

One party per web UI because a GCP backend authenticates as whatever
`GOOGLE_APPLICATION_CREDENTIALS` says, once per process — activating a MedPerf
profile does not change who the process is to Google. Switching party is
switching port.

Timing: about ten minutes of submissions — longer than the mock run, because
each party has a storage of its own and so downloads the benchmark's containers
for itself — a minute or two for each asset to be encrypted, uploaded and
authorized, and then one long step. *Run the benchmark*
starts the VM, waits for Confidential Space to boot, pull a multi-gigabyte image
and run it, streaming the serial console into the browser as it goes. **Fifteen
to thirty minutes is normal.** Do not interrupt it; the step's own ceiling is 90
minutes.

While it runs, this shows the same thing from outside:

```bash
gcloud compute instances get-serial-port-output mpcc-e2e-vm --zone=$MPCC_VM_ZONE | tail -40
```

## 8. What you should have at the end

```
<test root>/artifacts/run.mp4        the browser, start to end
<test root>/{benchmark,model,data}/webui.log
```

Check before reporting success. The video should be about as long as the run
took, and the collector's bucket should be holding what the VM wrote:

```bash
ffmpeg -hide_banner -i <test root>/artifacts/run.mp4 2>&1 | grep -E 'Duration|Stream'
gcloud storage ls "gs://$MPCC_COLLECTOR_BUCKET/**"
```

(If `ffmpeg` is not on `PATH`, the bundled one is
`python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`.)

The recording is real time, and most of a GCP run is one step waiting on a VM,
so expect half an hour of video. Hand over a faster copy alongside it:

```bash
ffmpeg -i run.mp4 -filter:v setpts=PTS/8 -an run_8x.mp4
```

Then give the person the path to `run.mp4`, the step count, and the run's
elapsed time.

## 9. When something fails

The script prints the failing step, the URL, a screenshot, the page HTML, and
the last 30 lines of each web UI's log. The video ends on the failure with the
step name in the caption bar.

| what you see | what it is |
| --- | --- |
| `(Role roles/…) User missing permissions … on <resource>` | step 3 did not grant it, or the ADC is not the account you think — re-run step 5 |
| `Failed to update workload identity pool provider` | pool admin was not granted; the terraform grants it through a local `gcloud` call, which needs gcloud authenticated as the master (step 2) |
| `Failed to run workload: User lacks permissions or VM does not exist` | wrong `vm_name`/`vm_zone`, or the data owner has no instance admin on the VM |
| the run step ends with `Workload did not complete successfully` | the workload ran and wrote nothing. The serial console says why — key release refused, or a hash it was told did not match what it read |
| key release refused in the serial console (403 from STS or KMS) | the attestation did not match the grant — see below |
| every step fails at the login page | the MedPerf server is not up, or its database was not reset |
| a step times out on a Configure button | the CC form has a field the test does not fill — go back to step 1 |
| the serial console shows the image pull failing | usually Docker Hub's anonymous pull limit on the VM's egress address; wait and run again |
| `Not recording: Xvfb is not installed` | step 7's first block |
| no `run.mp4` and no message | ffmpeg died; its error is printed where the video path would have been |

With `fix_problems=False`, stop at the first one and report it. With `True`,
fix it and start again from step 6 — a half-finished run leaves entities on the
MedPerf server that make the next one fail somewhere else.

### If the key is not released

This is the one failure that is specific to running on a real cloud, so it is
worth knowing how to read.

A workload identity pool rebuilds the workload's identity out of the
attestation, and the first term of it is
`assertion.submods.container.image_digest`. MedPerf pinned a digest when the
benchmark script container was submitted. If the two differ by one character,
KMS refuses and the workload writes nothing.

What MedPerf pinned is what this prints:

```bash
docker buildx imagetools inspect mlcommons/medperf-cc-chestxray:0.0.1 \
  --format '{{json .Manifest}}'
```

Note that this tag is an **image index**, not a single manifest: there is a
top-level `digest` and a per-platform one under `manifests`. MedPerf pins the
top-level one. What the Confidential Space launcher reports is in the VM's
serial console:

```bash
gcloud compute instances get-serial-port-output mpcc-e2e-vm --zone=$MPCC_VM_ZONE \
  | grep -i digest
```

If those are the same digest, the mismatch is elsewhere — the data or model
hash, or the collector's key. If they are *different* digests of the same
image, that is a real incompatibility between what MedPerf records and what
Confidential Space attests, and it is a finding worth reporting rather than
working around.

The other way this fails is simpler: the image on Docker Hub was re-pushed
after the benchmark was registered, so the digest MedPerf pinned is nobody's
image any more. Re-register the container and the benchmark.

## 10. Clean up

Delete the VM. It is the only thing that costs money when nothing is running:

```bash
gcloud compute instances delete mpcc-e2e-vm --zone=$MPCC_VM_ZONE --quiet
```

Empty the three buckets, but do not delete them:

```bash
for b in $MPCC_MODEL_BUCKET $MPCC_DATA_BUCKET $MPCC_COLLECTOR_BUCKET; do
  gcloud storage rm -r "gs://$b/**" 2>/dev/null || true
done
```

If step 4 had to create service account keys, delete them:

```bash
for role in model data; do
  sa=mpcc-e2e-$role-owner@$MPCC_PROJECT_ID.iam.gserviceaccount.com
  for key in $(gcloud iam service-accounts keys list --iam-account="$sa" \
                 --managed-by=user --format='value(name)'); do
    gcloud iam service-accounts keys delete "$key" --iam-account="$sa" --quiet
  done
done
rm -rf $WORK/adc
```

**Keep**: the buckets, the keyrings and keys, the workload identity pools, the
three service accounts, and `$WORK/terraform` with its state. Re-running this
recipe reuses all of it and only re-creates the VM.

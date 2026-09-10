# Running this on real GCP confidential computing

The mock backend proves the plumbing. This runs it for real: the model is
decrypted, and the benchmark service's prompts are answered, only inside an
attested TDX VM.

Three roles. They can be three people or one person wearing three hats, but they
need **two GCP projects** — one for the data side, one for the model side.

| Role | Owns | GCP resources |
| --- | --- | --- |
| Data owner | the benchmark service account | bucket, KMS key, workload identity pool, service account, VM |
| Model owner | the weights | bucket, KMS key, workload identity pool |
| Collector | receives the grades | a bucket |

Data owner operates the VM and collects, which is the default.

---

## 1. Create the GCP resources

Run these in Cloud Shell, from `examples/cc/admin_scripts/terraform`. Edit
`config.tf` in each directory first — see that directory's `README.md`.

```bash
# Data side: the encrypted asset, the VM it runs on, the bucket results land in
( cd asset_owner      && terraform init && terraform apply && terraform output -raw info )
( cd operator_gpu     && terraform init && terraform apply && terraform output -raw info )
( cd result_collector && terraform init && terraform apply && terraform output -raw info )

# Model side
( cd asset_owner && terraform init && terraform apply && terraform output -raw info )
```

Each prints the values you need for step 3. Save that output. Copy a directory
before editing it if you are running the same one for both sides — Terraform
keeps its state there, and two roles cannot share one.

Run `result_collector` after `operator_gpu`: it needs the workload service
account that one creates. Use `operator_cpu` instead if you only want a CPU VM
— fine for a 0.5B model, far too slow for 7B.

**Quota:** `a3-highgpu-1g` (one H100). Request it before you start, it is not
granted by default.

---

## 2. Build and push the image

`mlcommons/medperf-safety-benchmark` is published and `container_config.yaml`
names it, so this step is only needed if you have changed anything under
`benchmark/`.

```bash
cd examples/safety_benchmark

IMAGE=us-docker.pkg.dev/PROJECT_ID/REPO/medperf-safety-benchmark:v1 \
  bash build.sh
```

Then point `container_config.yaml` at that same image name.

**The VM needs egress to the benchmark service.** That is where the prompts and
the grades come from; a run without it cannot start. Nothing else is fetched at
run time — the model is decrypted from the owner's bucket — so the boot disk
only has to hold the image and the weights.

---

## 3. Write the four config files

Copy from `examples/cc/chestxray/`, replace the values with what step 1 printed.

**`dataset_cc_config.json`** (data owner)

```json
{
  "backend": "gcp",
  "project_id": "...", "project_number": "...",
  "bucket": "...",
  "keyring_name": "...", "key_name": "...", "key_location": "us-west1",
  "wip": "...", "wip_provider": "attestation-verifier"
}
```

**`model_cc_config.json`** (model owner) — same shape, the model side's values.

**`operator_cc_config.json`** (data owner)

```json
{
  "backend": "gcp",
  "project_id": "...", "service_account_name": "...",
  "vm_zone": "...", "vm_name": "..."
}
```

**`collector_cc_config.json`**

```json
{ "backend": "gcp", "bucket": "..." }
```

Policies stay as they are in `examples/cc/chestxray/` — `dataset_cc_policy.json`
and `model_cc_policy.json`.

---

## 4. Register everything

Same sequence as `cli/cli_tests_cc_safety.sh`, which you can read as the
worked example. Once, as benchmark owner:

```bash
medperf container submit --name safety-prep -m prep/container_config.yaml \
                         -p prep/workspace/parameters.yaml --operational
medperf container submit --name safety-script -m container_config.yaml --operational
medperf model submit --name safety-reference --asset-url <URL to a weights tarball> --operational
medperf benchmark submit --name safety-bmk --description safety \
    --demo-url <URL to demo dataset tarball> \
    --data-preparation-container $PREP --reference-model $REF \
    --topology end_to_end_script --benchmark-script $SCRIPT --operational
```

The reference model must be a **URL**, not `--asset-path`. A local-path asset
requires CC, and the reference model gets run during compatibility tests against
datasets that are not CC-configured yet.

Both parties need an RSA certificate before any policy will sync:

```bash
medperf certificate get_client_certificate --key_type RSA
medperf certificate submit_client_certificate --key_type RSA -y
```

Model owner:

```bash
medperf model submit --name my-model --asset-path ./weights.tar.gz --operational
medperf model associate -m $MODEL -b $BMK -y
```

Data owner. The "dataset" is a folder holding one `connection.yaml` — the
benchmark service and the key that reaches it, as in `demo/raw/`. Both paths
are that same folder; there are no labels to point at:

```bash
medperf dataset submit -p $PREP -d ./connection -l ./connection \
                       --name baas --description "benchmark service" --location here -y
medperf dataset prepare -d $DSET
medperf dataset set_operational -d $DSET -y
medperf dataset associate -d $DSET -b $BMK -y
```

Benchmark owner approves both:

```bash
medperf association approve -b $BMK -d $DSET
medperf association approve -b $BMK -m $MODEL
```

---

## 5. Turn on confidential computing

Model owner:

```bash
medperf confidential configure_model_for_cc -m $MODEL -c model_cc_config.json -p model_cc_policy.json
medperf confidential update_model_cc_policy -m $MODEL
```

Data owner:

```bash
medperf confidential configure_dataset_for_cc -d $DSET -c dataset_cc_config.json -p dataset_cc_policy.json
medperf confidential update_dataset_cc_policy -d $DSET
medperf confidential setup_cc_collector -c collector_cc_config.json
medperf confidential setup_cc_operator -c operator_cc_config.json
```

`configure_*` encrypts the asset and uploads it. `update_*_cc_policy` is the
moment of consent — it binds the decryption key to this exact
(image, connection, model, collector). Re-run it whenever any of those change.

---

## 6. Run

```bash
medperf dataset run_benchmark -b $BMK -d $DSET
```

This starts the VM, streams its serial log, waits, then downloads and decrypts
the results. Then, separately:

```bash
medperf result submit -r $EXECUTION -y
```

If someone else operated the run, they cannot open the results. The collector
fetches them:

```bash
medperf confidential download_cc_results -e $EXECUTION
```

---

## Gotchas

- **The VM must be stopped before a run.** MedPerf starts it. The operator
  stack leaves it stopped; if a run dies, stop it by hand before retrying.
- **Re-run `update_*_cc_policy` after rebuilding the image.** The policy binds
  the image digest. A new build is a new identity and the key will not be
  released.
- **`MEDPERF_ON_PREM` must not be set.** It bypasses encryption entirely.
- **Never `--asset-url` the model under test.** That publishes the weights. Only
  the reference model uses a URL.
- **Check the proof** after collection — it is what tells you the reported
  numbers came from the image you approved:

  ```bash
  medperf result verify -e $EXECUTION
  ```

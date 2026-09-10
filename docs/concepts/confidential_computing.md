# Configuring confidential Computing

## Overview

You are a data owner. You already have a registered, prepared, operational dataset. You already associated your dataset with the benchmark that contains a model that requires confidential computing.
This guide helps you configure the MedPerf client to run a confidential computing model on your dataset in the google cloud environment.

## Start the web UI and login

Make sure you have MedPerf installed.

Run the command `medperf_webui` on your terminal to start the local web user interface.

In the web UI, login by clicking on the `login` button and follow the required steps.

## Get a certificate

1. Navigate to the `settings` page by clicking on the user icon on the top right.
2. Scroll down to the `Certificate Settings` section.
3. If you already have a certificate, skip this step. Otherwise, click the button and follow the required steps to get a certificate.

Note: you may see a status `to be uploaded`. No need to upload your certificate for this usecase.

## Configure your cloud environment information in MedPerf

Ask your cloud administrator for the following information:

- Project ID
- Project Number
- Bucket
- Keyring Name
- Key Name
- Key Location
- Workload Identity Pool
- Workload Identity Provider
- Service Account Name
- VM Zone
- VM Name
- Results Bucket — where results written for you land. Only needed if results
  are to be released to you, and a bucket of its own rather than the one above.

You will use this information to configure your Medperf client.

The Terraform configurations in
[`examples/cc/admin_scripts/terraform`](https://github.com/mlcommons/medperf/tree/main/examples/cc/admin_scripts/terraform)
create all of it, one directory per cloud role, and print exactly this list at
the end. Give that to your cloud administrator if they have not done it before.

### Set up google cloud CLI

Note: This step should be done in a terminal.

1. Install the gcloud CLI (<https://docs.cloud.google.com/sdk/docs/install-sdk#latest-version>). Follow only the two sections about installing the CLI and initializing google cloud.
2. Run `gcloud auth list` and make sure your account is active (an asterisk should be next to your account email)
3. Set the project ID by running the command `gcloud config set project PROJECT_ID` where `PROJECT_ID` is the project ID you got from your cloud admin.
4. Run the following command `gcloud auth application-default login` and follow the required steps.

### Configure Medperf with your confidential VM settings

Two settings, because they are two roles. Operating a workload is running the
machine; collecting is receiving what it produced. The same person usually does
both, and they are configured separately so that they need not.

1. Navigate to the `settings` page in the web UI
2. Scroll down to `Confidential Computing Operator Settings`
3. Check the box `Configure confidential Computing`
4. Pick a confidential runner, and fill in what it asks for.
5. Click `Configure`.
6. Scroll to `Confidential Computing Result Collector`, check its box, and
   name the bucket you want results written to. It has to be yours: results are
   encrypted for your key, and nobody else should be asked to hold them.

### Configure Medperf with your Dataset cloud resources settings

1. Navigate to your dataset dashboard (Click on the `Datasets` tab, then find your dataset. You can click `mine_only` to view only your datasets.)
2. Scroll down to the section `Confidential Computing Preferences`.
3. Check the box `Configure dataset for Confidential Computing`
4. Pick where the ciphertext lives and who may have the key, and fill in what each asks for.
5. Choose how narrowly your grant is scoped, under `Grant scope`. See below.
6. Click `Configure`.
7. After step 6, a new button will appear. Click on the new button `Sync CC policy`.

## Grant scope

Your grant names the workloads allowed to decrypt your asset. A workload is
identified by up to four hashes: the benchmark script's container image, the
dataset, the model, and the key the results are encrypted for.

Two of the four are never a choice. The benchmark script is always pinned —
without it, any container image could ask for your key. Your own asset is
always pinned — without it, a workload aimed at somebody else's asset could
use your grant to read yours.

The other two are yours to decide:

| Choice | Effect |
| --- | --- |
| Pin the {model, dataset} | Authorize one exact peer asset rather than any. You will have to sync again whenever a new one is approved for a benchmark. |
| Release results to | Whose keys results may be encrypted for. Naming any of them has the cloud check the key, and not just this client. |

A policy means the same thing whichever kind of asset it is attached to. There
is no separate default for a dataset and for a model: what the asset kind
decides is only which of the two asset hashes is your own and which is the
peer's.

Unconfigured, **the peer is pinned** — the narrower of the two, so that silence
never authorizes a peer you have not seen. **Collectors have no default at
all**: a policy that names nobody is refused rather than guessed, because
authorizing nobody is a policy no execution could satisfy and is far more likely
to be an owner who forgot than one who meant it.

Both choices are also available in the JSON policy file the CLI takes:

```json
{
    "bind_peer_asset": true,
    "allowed_result_collectors": ["data_owner", "benchmark_owner"]
}
```

`allowed_result_collectors` has to name at least one party. An empty list, or
leaving the key out, is rejected. Because it always names somebody, the
collector's key is always pinned in the cloud as well, not just checked by this
client.

### Who may collect results

`allowed_result_collectors` says who may *receive* the results of an execution
involving your asset — not who may run it. Anybody may run one; what the
policies control is where the output goes and whose key it is encrypted for.

Both asset owners have to name the same party, because there is one key and one
destination. MedPerf works out who that is from the two lists, and refuses the
execution when they name nobody in common, or more than one — that is not a
choice it can make on your behalf. The cloud refuses again afterwards, by
withholding the asset key from a workload writing for anyone else.

The benchmark owner does not get to decide this. They are not the party at
risk, and MedPerf has no way for them to enforce it; `benchmark_owner` is simply
one of the roles each asset owner may choose to accept — though nothing
publishes their key to the other parties yet, so naming only them will fail.

An `inference_script` benchmark is the exception: its predictions are scored
on-prem against ground truth labels only the data owner holds, so the data owner
both operates and collects one whatever the policies say.

### Running as a model owner

A data owner runs a benchmark's models against their dataset:

```bash
medperf benchmark run -b <benchmark-id> -d <dataset-id>
# or, from the dataset: medperf dataset run_benchmark -b <benchmark-id> -d <dataset-id>
```

A model owner runs the mirror of it — their one model against the benchmark's
datasets:

```bash
medperf model run_benchmark -b <benchmark-id> -m <your-model-id>
```

Naming no datasets takes every dataset the benchmark approved that is
configured for confidential computing; name them with `-d` (repeat the flag) or
`--datasets-from-file` to pick. Only the model's owner can run this, and only
for a model that runs inside a confidential VM: you never see the data, so
there is nothing to run anywhere else. The machine is yours and so is its bill.

It is also only for an `end_to_end_script` benchmark. An `inference_script` one
scores on-prem, for the reason just given, so its executions are the data
owner's to operate.

### When the operator is not the collector

Only an `end_to_end_script` benchmark can have them differ. The operator starts
the workload and stops there: the results are written to the collector's
storage, encrypted for the collector's key, and the operator can neither reach
them nor open them. The collector picks them up afterwards:

```bash
medperf confidential download_cc_results -e <execution-id>
```

In the web UI it is the `Collect results` button, which appears beside the model
on your dataset's page (and beside the dataset on your model's page) with a box
to type the execution id into.

The operator passes the execution id on — their own page shows it once the run
finishes. Nothing lists an execution waiting for you yet, which is why the
number has to be handed over.

## Choosing where everything lives

A confidential execution needs four things, and your configuration file picks a
provider for each:

| Service | What it is | Choices |
| --- | --- | --- |
| `storage` | where your asset's ciphertext lives | `gcp`, `mock` |
| `vault` | who may have the key that opens it | `gcp`, `mock` |
| `runner` | what starts the confidential workload | `gcp`, `mock` |
| `result_store` | where the results are written, and whose it is | `gcp`, `mock` |

Name one backend at the top level and it serves everything:

```json
{
    "backend": "gcp",
    "project_id": "...",
    "project_number": "...",
    "bucket": "...",
    "keyring_name": "...",
    "key_name": "...",
    "key_location": "...",
    "wip": "...",
    "wip_provider": "..."
}
```

Or give a service a section of its own, which inherits the shared settings and
overrides what it needs — the backend included, so an asset's ciphertext and
the key that opens it need not be with the same provider:

```json
{
    "backend": "gcp",
    "project_id": "...",
    "bucket": "...",
    "vault": {
        "keyring_name": "...",
        "key_location": "..."
    }
}
```

There is no default. A configuration that names no backend is refused rather
than guessed.

Backends are chosen per asset, so two assets configured differently can take
part in the same execution — as long as the benchmark script supports both.

### Trying it without a cloud account

`mock` keeps everything in a directory on this machine and runs the workload as
an ordinary container. Every step a real backend takes is taken — the asset is
encrypted, the key is stored apart from it, the permitted identities are written
down — so it is a faithful way to develop against, and it is what the
confidential computing integration tests run on.

```json
{
    "backend": "mock",
    "root": "/tmp/medperf_cc_mock"
}
```

It protects nothing at all. There is no confidential VM, nothing is attested,
and the key sits beside the ciphertext. Never point a real dataset at it.

## Checking a result afterwards

A confidential execution attests to what it computed. Before packing up the
results, the workload writes a statement naming the hashes of what went in and
what came out, and an attestation token whose nonce is that statement's hash.
Together they establish which script ran, on which inputs, producing exactly
these bytes, inside genuine confidential hardware — without anyone having to
trust whoever reported the number.

```bash
medperf result verify -e <execution-id>
```

The token carries its own certificate chain, which is checked against the
issuer's root certificate, fetched at the time you verify. Token expiry is
deliberately not checked: a proof records a run that already happened, and a
one-hour token that had to still be current would make every proof
self-destruct.

### What a proof does and does not establish

It establishes which script ran, on which inputs, producing exactly these metrics,
inside genuine confidential hardware. It does **not** establish that the script
computed the metric correctly — attestation pins which code ran, never that the
code is right. What mitigates that is the script being public with a pinned
image digest.

It is also topology dependent:

| Topology | What the proof covers |
| --- | --- |
| `end_to_end_script` | the reported metric, computed inside the VM — end to end |
| `inference_script` | nothing you can check: the metric is scored on-prem afterwards, and the VM attested to no metric of its own |
| `byo_inference_script` | nothing; no confidential VM is involved |

## What's next?

As a data owner, you can now run the model that required confidential computing, by clicking the button `Run` near the model of interest on your dataset's page. After execution finishes, submit the results by clicking the `Submit` button that will later appear.

As a model owner, your model's page lists the datasets of every benchmark it was approved for, with the same `Run` button beside each. It only appears for a model that runs inside a confidential VM, and it is greyed out until both sides are ready: the data owner has to have configured their dataset for confidential computing, and you have to have configured where your workloads run. Running one starts a machine in your own cloud account, and the results go to whoever the two policies release them to — which may not be you.

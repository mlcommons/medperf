# The confidential benchmark base image

What runs inside the confidential VM. A benchmark owner builds their script on
top of it and it takes care of everything around the benchmark itself: fetching
the encrypted inputs, opening them, checking they are what the operator
declared, attesting to what was computed, and encrypting the results for
whoever is collecting them.

## Building

```bash
bash build.sh          # takes nothing; builds and publishes the image
```

Not a bare `docker build`. The image carries the integrity proof contract -- how
a statement is encoded and how its hashes are taken -- as `src/statement.py`,
and that copy has to agree byte for byte with `cc/medperf_cc/statement.py`, the
same file whoever verifies a proof runs. Agreeing is what stops the producing
and the verifying side from drifting apart; a disagreement over one byte would
make every proof fail to verify with nothing to say why. `build.sh` compares
their hashes and refuses to build when they differ, naming the copy to make.

It is the only thing taken from `medperf_cc`, and it depends on nothing but the
standard library. Everything else here is deliberately reimplemented: this image
is the trusted computing base, and the rest of that package exists to set up
cloud resources, which is not something a confidential VM should be able to do.

## Modes

**Dev.** Set `MEDPERF_ON_PREM` and the container runs the benchmark directly on
mounted volumes, with none of the above.

**Production.** Everything comes from the environment, described below.

## Backends

Each service names its own backend, so one run can mix them. The image ships
`gcp` and `mock`, and a benchmark owner who supports fewer says so by leaving
them out of the registries in `src/assets/factory.py`.

`mock` reads what `medperf_cc`'s mock backends wrote in a directory on the host.
It exists for developing and testing without a cloud account, and gives no
protection at all: there is no confidential VM and nothing is attested.

## The environment a workload receives

`DATA_CONFIG` and `MODEL_CONFIG` say where an asset's ciphertext lives and who
releases its key. They carry no secrets — they travel here as VM metadata the
operator can read.

```json
{
    "storage": {"backend": "gcp", "bucket": "...", "object_path": "...",
                "workload_identity_pool_provider": "..."},
    "vault": {"backend": "gcp", "bucket": "...", "wrapped_key_path": "...",
              "key_name": "...", "workload_identity_pool_provider": "..."}
}
```

```json
{
    "storage": {"backend": "mock", "root": "...", "asset_name": "..."},
    "vault": {"backend": "mock", "root": "...", "asset_name": "...",
              "terms": ["script", "data", "model", "collector"]}
}
```

`RESULT_CONFIG` says where to put the output, in the operator's own backend.

`RESULT_COLLECTOR` is the base64 PEM public key the results are encrypted for.

`EXPECTED_DATA_HASH`, `EXPECTED_MODEL_HASH` and
`EXPECTED_RESULT_COLLECTOR_HASH` are what the workload was told it is running
on. They are also what a key release backend matches the attestation against,
which is why the image declares them under
`tee.launch_policy.allow_env_override`: nothing else may be overridden, so
nothing else can change what a workload's identity is.

The workload checks all three against what it actually read, and refuses to go
on if they differ.

## Attestation

Statements are versioned, and a verifier only accepts versions it knows. Both
numbers live together in `statement.py`, so raising one without the other is
visible in one place.

Requested from the launcher over `/run/container_launcher/teeserver.sock`. It is
the only attestation primitive a workload has: it cannot obtain raw hardware
evidence, so everything that needs to prove what this workload is goes through
there.

Used for two things — asking an on-prem key broker for a key, and signing the
integrity statement written beside the results. When the launcher is not there,
as under the mock runner, the results are still produced and the proof is simply
absent.

## Cloud environment requirements

```text
--attribute-condition="assertion.swname == 'CONFIDENTIAL_SPACE' \
    && 'STABLE' in assertion.submods.confidential_space.support_attributes"
```

Use a non-debug image: a debuggable one is refused.

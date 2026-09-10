# medperf-cc

Confidential computing components used by MedPerf.

Nothing here knows what a benchmark, a dataset or a model is, and nothing a
caller writes names a provider. A caller translates its own domain into a
workload identity and an asset policy, hands over the configuration an asset or
an operator carries, and these components resolve the rest.

## Layout

One folder per service, one folder per backend inside it:

```text
identity     what a workload is, what an owner grants, how much they pin
policy       where a workload must run, and how narrow the grant is
workload     the environment contract a confidential workload reads
attestation  verifying a Confidential Space token
statement    what a workload attests to, and how it is hashed
proof        checking that attestation against what you expected
asset        an asset's ciphertext, its key, and who may have them

storage/     service: where the ciphertext lives   gcp · mock
vault/       service: who may have the key         gcp · mock
runner/      service: running the workload         gcp · mock
result_store/  service: where the results land       gcp · mock
backends/    choosing one, and the plumbing they share, a folder each
```

Adding a provider is adding a folder under each service it offers. Nothing
outside `backends/` and those folders mentions one.

## Configuration

A configuration selects its own backends. Keys at the top level are shared by
every service, and a section named after a service adds to or overrides them —
the backend included, so an asset's two halves need not be with the same
provider:

```json
{"backend": "gcp", "project_id": "p", "bucket": "b", "keyring_name": "..."}
```

```json
{"backend": "gcp", "project_id": "p", "bucket": "b",
 "vault": {"keyring_name": "medperf", "key_location": "us-west1"}}
```

No backend is a default. An unnamed one is refused rather than guessed, because
guessing would send an asset somewhere its owner never chose — and because one
of the choices protects nothing at all.

## The one file that leaves this package

`statement.py` is the integrity proof contract: how a statement is encoded and
how the hashes in it are taken. The confidential base image copies it in at
build time and imports it as `statement`, so the producing and the verifying
side are one implementation rather than two that have to be kept in agreement.

That is why it imports nothing but the standard library. The image is the
trusted computing base, and cloud clients, IAM and pydantic have no business
running inside a confidential VM. Anything needing a dependency belongs in
`proof.py` or in the image, not there.

## The mock backend

`mock` does everything a real backend does — the asset is encrypted, the key is
kept apart from it, the permitted identities are written down — in a directory
on this machine. It exists so the whole flow can be developed and tested without
a cloud account, and so the abstraction has a second implementation keeping it
honest.

It offers no protection whatsoever: nothing is attested, nothing is verified,
and the workload runs as an ordinary container. That is why it has to be asked
for by name.

```json
{"backend": "mock", "root": "/tmp/medperf_cc_mock"}
```

## Two boundaries

- **Assets arrive already encrypted.** The key belongs to the asset owner, so
  there is no reason for it to pass through here.
- **Results leave still encrypted.** Only the party holding the result
  collector's private key can open them, and that party is not this code --
  nor, necessarily, whoever ran the workload. They land in the collector's own
  storage, which is why `result_store` is a service of its own rather than
  something the runner decides.

## Installing

```bash
pip install -e cc/
```

Not published to PyPI, so anything depending on it installs it from source.

## Tests

```bash
cd cc && pytest tests/
```

`tests/test_producer_contract.py` is the odd one out: it loads the confidential
base image's proof producer from source, with `statement` bound to the module
above, exactly as the image runs it. What it checks is what the producer decides
on its own -- which keys go in a statement, where the measurements come from,
what a workload that produced no metrics attests to. Keep it passing.

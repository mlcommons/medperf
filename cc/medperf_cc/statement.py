"""The integrity statement, as both sides of it have to agree it is spelled.

A workload writes a statement naming what it consumed and what it produced, and
an attestation token whose nonce is that statement's hash. Whoever checks the
proof later recomputes both from what they hold. If the two sides disagreed
about a single byte of the encoding, every genuine proof would fail to verify
with nothing to say why.

So this file is the contract, and it is the same file on both sides. It is what
the confidential base image copies in and imports as `statement`, which is why
it depends on nothing but the standard library: the image is the trusted
computing base, and the rest of this package -- cloud clients, IAM, pydantic --
has no business running inside a confidential VM.

Keep it that way. Anything needing a dependency belongs in `medperf_cc.proof`
(verifying) or the image's `integrity_proof.py` (producing), not here.

`json_safe` below has a deliberate twin in the MedPerf client, which applies the
same mapping to everything it submits to the server -- see
`medperf.utils.sanitize_json`. It is written out twice rather than imported so
that MedPerf stays installable without these components. The two must agree: a
result the client mapped one way and a workload attested to another way could
not be verified against its own proof.

## The result hash

`results_sha256` covers the metrics as a *value*: `results.yaml` parsed, then
hashed canonically. That is what MedPerf uploads to its server and serves back
as JSON, so anybody holding nothing but the reported numbers can recompute this
-- which is the point, since the output files themselves stay with whoever ran
the workload. Hashing the file's bytes would not do either: YAML formatting and
key order would have to survive a round trip through a database to match.
"""

import hashlib
import json
import math

STATEMENT_FILE = "integrity_statement.json"
TOKEN_FILE = "integrity_token.jwt"

# The one file MedPerf reads a benchmark's metrics out of. Absent for a topology
# whose workload produces predictions rather than a score.
RESULTS_FILE = "results.yaml"

# A proof is meant to be checkable by anyone, so there is no particular relying
# party to name. A fixed, recognizable audience beats a misleading one.
PROOF_AUDIENCE = "https://medperf.org/integrity-proof"

# What a workload writes today, and what a verifier still knows how to read.
# They live together so that raising one without the other is visible here.
STATEMENT_VERSION = 2
SUPPORTED_STATEMENT_VERSIONS = {2}


def json_safe(value):
    """A value with everything JSON cannot spell taken out.

    Only non-finite floats, which is what a metric like an undefined AUC comes
    out as. Python writes them as bare `NaN` and `Infinity`, which no other JSON
    reader accepts -- PostgreSQL rejects them outright -- so a hash taken over
    them could not be recomputed by anybody else, which is the whole point of
    taking it. They become null, which is what survives the round trip anyway.

    !! This function has a twin: `medperf.utils.sanitize_json` in the MedPerf
    !! client, which applies this same mapping to every result it submits to
    !! the server. THE TWO MUST AGREE, VALUE FOR VALUE. A workload attests to
    !! the metrics as mapped here; a verifier later reads them back off the
    !! server as mapped there. If the mappings differ by so much as one value,
    !! the hashes differ, and `medperf result verify` reports the results as not
    !! matching their proof -- which reads like tampering rather than like a
    !! bug. Exactly that happened once: this mapped NaN to null while the client
    !! mapped it to the string "nan".
    !!
    !! They are written out twice rather than shared so that MedPerf stays
    !! installable without the confidential computing components. Change one and
    !! you must change the other.
    """
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def canonical_hash(value) -> str:
    """A hash of a value that does not depend on how it was serialized."""
    canonical = json.dumps(
        json_safe(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def statement_hash(statement: dict) -> str:
    """The nonce the workload committed to."""
    return canonical_hash(statement)

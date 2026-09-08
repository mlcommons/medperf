"""Producing an integrity proof for what this workload computed.

A benchmark result is otherwise a number the operator reports, and everybody
downstream has to take their word for it. This makes it checkable: a statement
naming what went in and what came out, bound to a signed attestation of what
actually ran, verifiable afterwards by anyone holding a pinned root certificate.

No new signing machinery is involved, because the attestation token already
carries most of the statement:

    submods.container.image_digest                       which script ran
    submods.container.env_override.EXPECTED_DATA_HASH    which data it declared
    submods.container.env_override.EXPECTED_MODEL_HASH   which model it declared
    swname / hwmodel / support_attributes                that it was real hardware
    eat_nonce                                            whatever we put there

So the statement's hash goes in the nonce, and the statement travels with the
results. What the token does *not* carry is the inputs as the workload actually
saw them -- `env_override` is operator-supplied and states an expectation, not a
fact. `setup_assets` measures the decrypted inputs and records what it found;
the statement reports those measurements, so a verifier can see the declared and
the measured values agree without having to know that the script checks them.

Only the producing is here. How a statement is encoded and how the hashes are
taken live in `statement.py`, which is `medperf_cc/statement.py` verbatim --
whoever verifies this proof runs that same file. It is copied in at build time
rather than edited here.
"""

import argparse
import json
import os
from typing import Optional

import yaml

from assets.attestation import AttestationUnavailable, request_token
from statement import (
    PROOF_AUDIENCE,
    RESULTS_FILE,
    STATEMENT_FILE,
    STATEMENT_VERSION,
    TOKEN_FILE,
    canonical_hash,
    statement_hash,
)

MEASURED_HASHES_FILE = "measured_hashes.json"


def results_hash(results_path: str) -> Optional[str]:
    """Hashes the metrics as a value, or None if this workload produced none.

    Parsed before hashing, so what is attested to is what MedPerf will upload
    and anyone can recompute -- not the bytes of a file nobody downstream
    keeps."""
    path = os.path.join(results_path, RESULTS_FILE)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return canonical_hash(yaml.safe_load(f))


def build_statement(results_path: str) -> dict:
    """The hashes of everything involved: what went in, and what came out.

    Data and model are measured inside the VM on the decrypted inputs, so they
    say what was actually read rather than what the operator declared. The
    script is deliberately not in here -- it comes from the token's attested
    `image_digest`, and a workload self-reporting its own image would be worth
    nothing.
    """
    measured = __measured_hashes()
    return {
        "version": STATEMENT_VERSION,
        "results_sha256": results_hash(results_path),
        "data_sha256": measured.get("data_sha256"),
        "model_sha256": measured.get("model_sha256"),
    }


def write_proof(
    results_path: str, token_type: str = "PKI", issuer: str = "google"
) -> Optional[str]:
    """Writes the statement and its attestation into the results directory.

    Returns None if the launcher would not issue a token. A workload that cannot
    prove itself should still deliver its results: an absent proof is visible to
    whoever checks, whereas raising here would turn "unverifiable" into "failed",
    which is the worse trade.
    """
    statement = build_statement(results_path)
    nonce = statement_hash(statement)

    try:
        # PKI by default: the token carries its own certificate chain, so the
        # proof can be checked years later against a pinned root, with no
        # network and regardless of signing key rotation.
        token = request_token(
            audience=PROOF_AUDIENCE,
            nonces=[nonce],
            token_type=token_type,
            issuer=issuer,
        )
    except (AttestationUnavailable, ValueError) as e:
        print(f"WARNING: no integrity proof will be produced: {e}")
        return None

    with open(os.path.join(results_path, STATEMENT_FILE), "w") as f:
        json.dump(statement, f, sort_keys=True, separators=(",", ":"))
    with open(os.path.join(results_path, TOKEN_FILE), "w") as f:
        f.write(token)
    return nonce


def __measured_hashes() -> dict:
    path = os.path.join(os.getenv("TMP_FILES", "/tmp/files"), MEASURED_HASHES_FILE)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write an integrity proof")
    parser.add_argument("--result-files", required=True)
    parser.add_argument("--token-type", default=os.getenv("PROOF_TOKEN_TYPE", "PKI"))
    parser.add_argument("--issuer", default=os.getenv("PROOF_ISSUER", "google"))
    args = parser.parse_args()

    written = write_proof(
        args.result_files, token_type=args.token_type, issuer=args.issuer
    )
    print("Integrity proof written" if written else "Integrity proof unavailable")

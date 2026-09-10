"""Checking that a result is what it claims to be.

A workload writes a statement naming what it consumed and what it produced, and
an attestation token whose nonce is that statement's hash. Together they
establish which script ran, on which inputs, producing exactly these metrics,
inside genuine confidential hardware -- without trusting whoever reported them.

Not established: that the script computed the metric correctly. Attestation
pins which code ran, never that the code is right.

Verification is offline for PKI tokens. Expiry is deliberately not checked: a
proof records a run that already happened, and a one-hour token that had to
still be current would make every proof self-destruct.

How the hashes are taken is not decided here. It is decided in
`medperf_cc.statement`, which the confidential base image copies in and runs as
its own, so that the two sides cannot drift apart.
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import BaseModel

from medperf_cc.attestation.authority import GOOGLE, trust_anchor
from medperf_cc.attestation.token import AttestationToken, TokenType
from medperf_cc.attestation.verifier import AttestationRequirements, verify_token
from medperf_cc.errors import AttestationError
from medperf_cc.statement import (
    PROOF_AUDIENCE,
    STATEMENT_FILE,
    SUPPORTED_STATEMENT_VERSIONS,
    TOKEN_FILE,
    canonical_hash,
    statement_hash,
)


def results_hash(results: dict) -> str:
    """Hashes the metrics themselves, as a value rather than as a file.

    This is the number everyone downstream actually sees: MedPerf parses
    `results.yaml`, uploads the result as a dict, and serves it back as JSON.
    Hashing the parsed value rather than the file's bytes is what lets anybody
    holding that dict recompute this -- no files, no YAML formatting, no
    knowledge of how it was written.
    """
    return canonical_hash(results)


@dataclass
class IntegrityProof:
    statement: dict
    token: str

    @classmethod
    def from_results_dir(cls, results_path: str) -> Optional["IntegrityProof"]:
        """Reads a proof, or None if the workload did not produce one."""
        statement_path = os.path.join(results_path, STATEMENT_FILE)
        token_path = os.path.join(results_path, TOKEN_FILE)
        if not (os.path.exists(statement_path) and os.path.exists(token_path)):
            return None

        with open(statement_path) as f:
            statement = json.load(f)
        with open(token_path) as f:
            return cls(statement=statement, token=f.read().strip())

    @classmethod
    def fromdict(cls, payload: dict) -> "IntegrityProof":
        return cls(statement=payload["statement"], token=payload["token"])

    def todict(self) -> dict:
        return {"statement": self.statement, "token": self.token}


class ProofExpectations(BaseModel):
    """What the results are supposed to be, according to the caller's records.

    Taking any of these from the proof itself would establish nothing, so they
    come from whoever is asking. All of them are required, and none of them may
    be None: every check below compares the proof against one of these, so a
    missing one would be a check that passes on an absence. "Nothing to compare
    against" is not the same answer as "matches", which is why these are
    validated into existence rather than defaulted.
    """

    script_image_hash: str
    data_hash: str
    model_hash: str
    # The metrics as a value -- what the server holds, and what anybody can
    # check without having run anything.
    results: dict

    class Config:
        # A misspelled field would be an expectation nothing compares against,
        # which is the failure this class exists to make impossible.
        extra = "forbid"


@dataclass
class ProofVerdict:
    verified: bool
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    token: Optional[AttestationToken] = None

    @property
    def summary(self) -> str:
        if self.verified:
            return "Results are backed by a valid integrity proof"
        return "; ".join(self.failures) or "Integrity proof could not be verified"


def verify_proof(
    proof: IntegrityProof,
    expectations: ProofExpectations,
    authority: str = GOOGLE,
) -> ProofVerdict:
    """Verifies a proof and reports every check, passed or failed.

    `authority` names who signed the attestation; what to accept as proof that
    the signature is genuine follows from it, and is fetched here.

    Collects failures rather than raising on the first, because which part is
    wrong is the useful output: a results hash that does not match means
    something quite different from an image digest that does not match. Not
    being able to reach the authority at all is different again, and raises:
    that is a proof nobody checked, not a proof that failed.
    """
    anchor = trust_anchor(authority)
    verdict = ProofVerdict(verified=False)

    try:
        token = verify_token(
            proof.token,
            anchor,
            AttestationRequirements(
                audience=PROOF_AUDIENCE,
                nonce=statement_hash(proof.statement),
                allowed_token_types=[TokenType.PKI, TokenType.OIDC],
                # A proof is a record of a run that already happened.
                check_expiry=False,
            ),
        )
    except AttestationError as e:
        verdict.failures.append(str(e))
        return verdict

    verdict.token = token
    verdict.checks.append("Attestation token is genuine and signed by the issuer")
    verdict.checks.append("Statement is the one the workload committed to")

    __check_statement_version(proof.statement, verdict)
    __check_results(proof.statement, expectations, verdict)
    __check_script(token, expectations, verdict)
    __check_inputs(proof.statement, token, expectations, verdict)

    verdict.verified = not verdict.failures
    return verdict


def __check_statement_version(statement: dict, verdict: ProofVerdict):
    version = statement.get("version")
    if version not in SUPPORTED_STATEMENT_VERSIONS:
        verdict.failures.append(f"Unsupported integrity statement version {version!r}")


def __check_results(
    statement: dict, expectations: ProofExpectations, verdict: ProofVerdict
):
    """That the reported metrics are the ones the workload computed.

    Checked as a value, so anybody reading the numbers off the server can do it
    -- no output files, no knowledge of how they were written."""
    attested = statement.get("results_sha256")
    actual = results_hash(expectations.results)
    if attested is None:
        verdict.failures.append(
            "The workload attested to no metrics, so the reported ones"
            " cannot be checked against it"
        )
    elif actual != attested:
        verdict.failures.append(
            "Reported metrics do not match the proof: the statement attests"
            f" to {attested}, these metrics hash to {actual}"
        )
    else:
        verdict.checks.append(
            "Reported metrics are exactly the ones the workload computed"
        )


def __check_script(
    token: AttestationToken, expectations: ProofExpectations, verdict: ProofVerdict
):
    """Which code ran. Taken from the attested image digest, never from the
    statement: a workload self-reporting its own image would be worth nothing."""
    if token.image_digest != expectations.script_image_hash:
        verdict.failures.append(
            f"Results were produced by image {token.image_digest}, not the"
            f" expected script {expectations.script_image_hash}"
        )
    else:
        verdict.checks.append("Produced by the expected script image")


def __check_inputs(
    statement: dict,
    token: AttestationToken,
    expectations: ProofExpectations,
    verdict: ProofVerdict,
):
    """What it ran on, declared and measured.

    The declaration is operator-supplied and lives in the attested environment;
    the measurement was taken inside the VM on the decrypted input. Agreement is
    what makes the declaration trustworthy without knowing the asset owners'
    policies."""
    environment = token.env_override
    inputs = (
        ("data", expectations.data_hash, "EXPECTED_DATA_HASH", "data_sha256"),
        ("model", expectations.model_hash, "EXPECTED_MODEL_HASH", "model_sha256"),
    )

    for label, expected, claim, measured_key in inputs:
        declared = environment.get(claim)
        if declared != expected:
            verdict.failures.append(
                f"Workload ran on a different {label}: attested {declared},"
                f" expected {expected}"
            )
            continue

        measured = statement.get(measured_key)
        if measured is not None and measured != expected:
            verdict.failures.append(
                f"The {label} the workload measured ({measured}) is not the one"
                f" it declared ({expected})"
            )
        else:
            verdict.checks.append(f"Ran on the expected {label}")

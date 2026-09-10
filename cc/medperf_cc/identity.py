"""What a confidential workload is, and which parts of it an asset owner pins.

Three things, kept apart on purpose:

    WorkloadIdentity  what one workload is -- every term, always
    WorkloadGrant     what an owner authorizes -- may leave a term out, and
                      then covers every value of it
    WorkloadScope     how much of a workload that owner pins

An authorization is not an identity. It is the projection of one onto the terms
its owner chose to look at: a `::`-joined string of hashes in one fixed order.
Both sides produce it the same way -- the owner from what they authorize, a key
release backend from an attestation. If the two ever disagreed about which term
is which, nothing would error; every authorization would silently stop matching.

An identity also carries the ids naming where a launched workload's output
goes. They take no part in any of the above.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from medperf_cc.errors import InternalError

SCRIPT_TERM = "script"
DATA_TERM = "data"
MODEL_TERM = "model"
COLLECTOR_TERM = "collector"

# The order is what makes two identity strings comparable at all.
TERM_ORDER = [SCRIPT_TERM, DATA_TERM, MODEL_TERM, COLLECTOR_TERM]

# Where each term is found in a Confidential Space attestation. These are token
# claim paths, which every key release backend reads one way or another: one
# has the cloud evaluate them, another looks them up in the token itself.
TERM_CLAIMS = {
    SCRIPT_TERM: "submods.container.image_digest",
    DATA_TERM: "submods.container.env_override.EXPECTED_DATA_HASH",
    MODEL_TERM: "submods.container.env_override.EXPECTED_MODEL_HASH",
    COLLECTOR_TERM: "submods.container.env_override.EXPECTED_RESULT_COLLECTOR_HASH",
}

# The field of a `WorkloadIdentity` each term is taken from.
TERM_FIELDS = {
    SCRIPT_TERM: "script_hash",
    DATA_TERM: "data_hash",
    MODEL_TERM: "model_hash",
    COLLECTOR_TERM: "result_collector_hash",
}


class AssetKind(Enum):
    DATA = "data"
    MODEL = "model"

    @property
    def own_term(self) -> str:
        return DATA_TERM if self is AssetKind.DATA else MODEL_TERM

    @property
    def peer_term(self) -> str:
        return MODEL_TERM if self is AssetKind.DATA else DATA_TERM


# The ids a launched workload carries. Never attested, and never part of any
# authorization -- they exist only to name where its output goes.
STORAGE_IDS = ("script_id", "data_id", "model_id", "execution_id")


class WorkloadIdentity(BaseModel):
    """What one workload is: every term of it, always.

    A workload always runs a script, on a dataset, with a model, for somebody's
    key. None of those can be absent, so none of the hashes can be. What may be
    absent is how much of it an asset owner chose to pin -- and that is a
    `WorkloadScope`, not an identity.

    The ids are a different matter. They say nothing about what the workload
    is, only where its output goes, so they are absent until it is actually
    launched. Anything that needs them says so by asking for
    `storage_prefix`.
    """

    script_hash: str
    data_hash: str
    model_hash: str
    result_collector_hash: str

    script_id: Optional[int] = None
    data_id: Optional[int] = None
    model_id: Optional[int] = None
    execution_id: Optional[int] = None

    class Config:
        # A misspelled hash would be dropped and the term left empty, which is
        # a different identity, not an error. Nothing downstream could tell:
        # the grant would simply stop matching the run.
        extra = "forbid"

    @property
    def storage_prefix(self) -> str:
        """Where this workload's output goes.

        The execution is in the path because everything else about two runs of
        the same triple is identical, and without it the second would overwrite
        the first -- so a missing id is not something to paper over with a
        shorter prefix."""
        missing = [name for name in STORAGE_IDS if getattr(self, name) is None]
        if missing:
            raise InternalError(
                f"This workload was built without {', '.join(missing)}, so it"
                " has no storage location. Only a launched workload has one."
            )
        return (
            f"d{self.data_id}-m{self.model_id}"
            f"-s{self.script_id}-e{self.execution_id}"
        )

    @property
    def results_path(self) -> str:
        return f"{self.storage_prefix}/output"

    @property
    def results_encryption_key_path(self) -> str:
        return f"{self.storage_prefix}/encryption_key"


class WorkloadGrant(BaseModel):
    """One authorization an asset owner publishes.

    Not an identity, because it may describe many workloads: an owner who did
    not pin the peer asset leaves it out, and the grant then covers every peer
    that could take its place. Which terms may be left out is decided by their
    `WorkloadScope`, and asking for a grant that omits a term the scope pins is
    an error rather than an empty hash quietly standing in for a real one.
    """

    # Both are pinned by every policy, so no grant can omit them.
    script_hash: str
    result_collector_hash: str
    # Absent when this owner did not pin that asset.
    data_hash: Optional[str] = None
    model_hash: Optional[str] = None

    class Config:
        extra = "forbid"


class WorkloadScope(BaseModel):
    """How much of a workload one asset owner pins, in canonical order.

    An owner does not authorize identities; they authorize as much of one as
    they chose to look at. That projection is what a backend stores and what it
    matches an attestation against, and both sides must produce it the same way
    or every grant silently stops matching.

    Built from an `AssetPolicy`, which decides how many terms there are; the
    order they come in is fixed here."""

    terms: List[str]

    def pins(self, term: str) -> bool:
        return term in self.terms

    def uid_of(self, grant: WorkloadGrant) -> str:
        """What this owner's authorization is written as.

        Refuses a grant that says nothing about a term this scope pins: an
        absent hash is not a wildcard, and joining it as an empty string would
        publish an authorization nobody could ever match."""
        missing = [
            term for term in self.terms if not getattr(grant, TERM_FIELDS[term], None)
        ]
        if missing:
            raise ValueError(
                f"This scope pins {', '.join(missing)}, so a grant has to name"
                f" {'them' if len(missing) > 1 else 'it'}"
            )
        return "::".join(getattr(grant, TERM_FIELDS[term]) for term in self.terms)

    def uid_from_claims(self, claims: dict) -> str:
        """The same string, read out of an attestation a workload presented.

        Byte for byte what `uid_of` produces, which is what lets a backend that
        evaluates the policy itself match one written for a backend that has
        the cloud evaluate it."""
        return "::".join(
            str(claim_at(claims, TERM_CLAIMS[term]) or "") for term in self.terms
        )


def claim_at(claims: dict, path: str):
    """Reads a dotted claim path out of a decoded token."""
    value = claims
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value

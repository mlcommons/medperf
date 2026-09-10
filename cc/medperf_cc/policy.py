"""What an asset owner will let a confidential workload do with their asset.

Stated in terms of the workload, never of a particular cloud: each key release
backend translates this into whatever it enforces policy with.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, validator

from medperf_cc.identity import (
    COLLECTOR_TERM,
    SCRIPT_TERM,
    TERM_ORDER,
    AssetKind,
    WorkloadScope,
)


class Party(Enum):
    """A role in a confidential execution, identified by that party's key."""

    BENCHMARK_OWNER = "benchmark_owner"
    MODEL_OWNER = "model_owner"
    DATA_OWNER = "data_owner"


# Whose key is pinned when an owner releases results to "the other side". The
# peer of a dataset is a model, and the party behind it is its owner.
PEER_PARTY = {AssetKind.DATA: Party.MODEL_OWNER, AssetKind.MODEL: Party.DATA_OWNER}


class AssetPolicy(BaseModel):
    """Where a workload must run, and how narrowly the grant is scoped.

    An owner always pins the benchmark script and their own asset: anything
    less would let an arbitrary image, or an image aimed at somebody else's
    asset, decrypt theirs. The remaining two terms of a workload's identity are
    theirs to choose.

    A policy means the same thing whichever kind of asset it is attached to.
    What differs between a dataset and a model is only which term is their own
    and which is the peer's, and that follows from the asset, not from the
    policy.
    """

    # The cloud region or zone the confidential VM must be running in.
    location: Optional[str] = None
    # The confidential hardware platform, as the attestation reports it.
    hardware: Optional[str] = None
    # Whether to pin the other asset in the execution, rather than allow any.
    # Pinning is the default: an owner who has not said otherwise authorizes
    # one exact combination, never any peer that comes along.
    bind_peer_asset: bool = True
    # Whose keys this owner will let results be encrypted for. Results are
    # encrypted for whoever operates the execution, so this is really the list
    # of who may operate one involving this asset. It has to name somebody:
    # authorizing nobody is a policy no execution could ever satisfy, and it is
    # far more likely to be an owner who forgot than one who meant it.
    allowed_result_collectors: Optional[List[Party]] = None

    class Config:
        # A policy decides who may read an asset. A key the owner misspelled is
        # a policy they did not get, so it is refused rather than ignored.
        extra = "forbid"

    @validator("allowed_result_collectors", always=True)
    def at_least_one_collector(cls, parties):
        """Refused rather than defaulted: who may read an asset's results is
        not something to guess on an owner's behalf."""
        if not parties:
            raise ValueError(
                "name at least one party allowed to collect results."
                f" One or more of: {', '.join(party.value for party in Party)}"
            )
        return list(dict.fromkeys(parties))

    def needs_peer(self, kind: AssetKind) -> bool:
        """Whether a grant for this asset has to be written out per peer.

        Pinning the peer plainly does: each peer is a different workload. So
        does releasing results to the peer's owner, for a less obvious reason
        -- what gets pinned is that owner's key, and which owner that is
        depends on which peer takes part. An owner doing neither writes one
        grant that covers every peer.
        """
        return self.bind_peer_asset or PEER_PARTY[kind] in (
            self.allowed_result_collectors or []
        )

    def scope(self, kind: AssetKind) -> WorkloadScope:
        """Which terms of a workload's identity this owner pins.

        `kind` says which asset the policy is protecting -- that is what makes
        one of the two asset terms "own" and the other "peer". It is not a
        second source of policy.

        The collector is always pinned, because a policy always names one."""
        terms = {SCRIPT_TERM, kind.own_term, COLLECTOR_TERM}
        if self.bind_peer_asset:
            terms.add(kind.peer_term)
        return WorkloadScope(terms=[term for term in TERM_ORDER if term in terms])

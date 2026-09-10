"""Whoever the results of a confidential execution are for.

The operator supplies the machine. The collector is the party whose key the
results are encrypted for and whose storage they are written to, and only they
can ever open them -- which is what lets the two be different people.

A party, not a backend: `medperf_cc.ResultStore` is the place the results land,
built from the `settings` below.
"""

import base64
from dataclasses import dataclass
from typing import Tuple

from pydantic import ValidationError

import medperf.config as medperf_config
from medperf.account_management import get_medperf_user_object
from medperf.cc.config import policy_of
from medperf.cc.parties import (
    certificate_of,
    current_user_public_key,
    is_current_user,
    party_owners,
)
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.model import Model
from medperf.exceptions import ExecutionError, MedperfException
from medperf.utils import get_string_hash
from medperf_cc import Party


@dataclass
class CollectorParty:
    user_id: int
    party: Party
    public_key: bytes
    settings: dict

    @property
    def key_hash(self) -> str:
        """The identity the workload attests the results are for."""
        return get_string_hash(self.public_key)


def collector_role(
    benchmark: Benchmark, dataset: Dataset, model: Model
) -> Tuple[int, Party]:
    """Which party both asset owners will release results to.

    The policies are the source of truth for this, and the only one: they say
    who an execution's results were encrypted for, and they said so before the
    execution existed. Nothing recorded afterwards is consulted here.

    Each owner names the roles they accept; the results are encrypted for a
    single key, so it has to be a role they both named. Two candidates is not a
    choice this can make on anybody's behalf, and none means the owners have
    not agreed -- both are refused rather than guessed at.
    """
    owners = party_owners(benchmark, dataset, model)
    accepted = [
        party
        for party in policy_of(dataset).allowed_result_collectors
        if party in policy_of(model).allowed_result_collectors
    ]

    # Two roles held by one person are one candidate, not two.
    candidates = {}
    for party in accepted:
        owner_id = owners.get(party)
        if owner_id is not None:
            candidates.setdefault(owner_id, party)

    if not candidates:
        raise ExecutionError(
            "The dataset owner and the model owner have not agreed on anybody"
            " to release results to. The dataset owner accepts"
            f" {__roles(dataset)}; the model owner accepts {__roles(model)}."
        )
    if len(candidates) > 1:
        named = ", ".join(sorted(party.value for party in candidates.values()))
        raise ExecutionError(
            f"Both asset owners release results to more than one party: {named}."
            " Results are encrypted for a single key, so exactly one of them"
            " has to be chosen. Narrow one of the policies."
        )

    return next(iter(candidates.items()))


def collects_results(
    user_id: int, benchmark: Benchmark, dataset: Dataset, model: Model
) -> bool:
    """Whether an execution of this pair would release its results to this user.

    The cheap half of `resolve_collector`, with no network in it, so a page may
    ask it about every model. Every reason for "no" looks alike here;
    `collector_role` is where they are told apart.
    """
    try:
        collector_id, _ = collector_role(benchmark, dataset, model)
    except (MedperfException, ValidationError):
        return False
    return collector_id == user_id


def resolve_collector(
    benchmark: Benchmark, dataset: Dataset, model: Model
) -> CollectorParty:
    """The collecting party, with the key results are encrypted for and the
    store they are written to.

    `collector_role` answers who; this adds what is needed to actually reach
    them, which costs a certificate listing and their published settings. Ask
    for the role alone when that is all you need."""
    user_id, party = collector_role(benchmark, dataset, model)
    return CollectorParty(
        user_id=user_id,
        party=party,
        public_key=__public_key(benchmark, user_id, party),
        settings=__settings(user_id, party),
    )


def __roles(entity) -> str:
    return ", ".join(
        party.value for party in policy_of(entity).allowed_result_collectors
    )


def __public_key(benchmark: Benchmark, user_id: int, party: Party) -> bytes:
    if is_current_user(user_id):
        return current_user_public_key()
    certificate = certificate_of(benchmark.id, user_id, party)
    return base64.b64encode(certificate.public_key())


def __settings(user_id: int, party: Party) -> dict:
    """Where this collector receives results.

    Their own, wherever they are. The operator has to know it to tell the
    workload where to write, so it is read from what the server publishes about
    them rather than from anything they hand over -- and it carries an address
    only, never their credentials."""
    if is_current_user(user_id):
        metadata = get_medperf_user_object().metadata
    else:
        metadata = medperf_config.comms.get_user_metadata(user_id)

    settings = (metadata or {}).get("cc", {}).get("collector", {})
    if not settings:
        raise ExecutionError(
            f"Results are to be released to the {party.value}, but they have"
            " not configured anywhere to receive them."
        )
    return settings

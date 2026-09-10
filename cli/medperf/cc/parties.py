"""Who holds which role in a confidential execution, and whose key collects.

Results are encrypted for a public key, and an asset owner who pins the result
collector is pinning that key. This is where a MedPerf role becomes the hash of
a key, which is the only form the attestation ever sees it in.
"""

import base64
import logging
from typing import Dict, List, Optional, Set

from medperf.account_management import get_medperf_user_data, is_user_logged_in
from medperf.commands.certificate.utils import current_user_certificate_status
from medperf.entities.benchmark import Benchmark
from medperf.entities.certificate import Certificate
from medperf.entities.dataset import Dataset
from medperf.entities.model import Model
from medperf.enums import CryptoKeyType
from medperf.exceptions import ExecutionError, MedperfException
from medperf.utils import get_string_hash
from medperf_cc import AssetKind, Party


def public_key_hash(certificate: Certificate) -> str:
    """The result collector identity a workload attests with."""
    public_key_b64 = base64.b64encode(certificate.public_key())
    return get_string_hash(public_key_b64)


def current_user_certificate() -> Certificate:
    """The current user's certificate, issued or merely submitted.

    A certificate that has been issued but not yet uploaded is still the key
    results will be encrypted for, so a fresh user is not blocked on the
    upload."""
    status_dict = current_user_certificate_status(CryptoKeyType.RSA)
    user_cert = None
    if status_dict["should_be_submitted"]:
        user_cert = Certificate.get_local_user_certificate(CryptoKeyType.RSA)
    elif status_dict["no_action_required"]:
        user_cert = status_dict["user_cert_object"]

    if not user_cert:
        raise MedperfException(
            "User must have a certificate to take part in a confidential execution"
        )
    return user_cert


# Which listing publishes a party's key to the other participants. The
# benchmark owner appears in neither, so nothing exposes their key yet.
PARTY_LISTINGS = {
    Party.DATA_OWNER: AssetKind.DATA,
    Party.MODEL_OWNER: AssetKind.MODEL,
}


def is_current_user(user_id: int) -> bool:
    """Whether this id is the person running the command.

    Their own certificate is read locally -- it may have been issued but not
    yet uploaded, and it is theirs to read either way."""
    return is_user_logged_in() and user_id == get_medperf_user_data()["id"]


def certificates_in(benchmark_id: int, side: AssetKind) -> List[Certificate]:
    """Every valid certificate on one side of a benchmark.

    Nobody may read another user's certificate in general, and rightly so. What
    they may read is the certificates of the parties they are already in a
    benchmark with, through a listing scoped to it -- a data owner sees the
    model owners, a model owner sees the data owners. So which listing to ask
    for follows from which side is wanted.

    The one lookup both sides go through: a grant pins the hash of a key, and
    an execution encrypts for that same key, so reading them two different ways
    could pin a hash the workload never presents.
    """
    if side is AssetKind.MODEL:
        certificates, _ = Certificate.get_benchmark_models_certificates(benchmark_id)
    else:
        certificates, _ = Certificate.get_benchmark_datasets_certificates(benchmark_id)
    return [certificate for certificate in certificates if certificate.is_valid]


def certificate_of(benchmark_id: int, user_id: int, party: Party) -> Certificate:
    """One named party's certificate in one benchmark."""
    side = PARTY_LISTINGS.get(party)
    if side is None:
        raise ExecutionError(
            f"Results are to be released to the {party.value}, but nothing"
            " publishes their key to the other parties. Name a dataset or"
            " model owner instead."
        )
    for certificate in certificates_in(benchmark_id, side):
        if certificate.owner == user_id:
            return certificate
    raise ExecutionError(
        f"Results are to be released to the {party.value}, but they hold no"
        " certificate in this benchmark, so there is no key to encrypt for."
    )


def peer_key_hashes(benchmark_id: int, peer: AssetKind) -> Dict[int, str]:
    """The key hash of every owner on the other side of one benchmark."""
    return {
        certificate.owner: public_key_hash(certificate)
        for certificate in certificates_in(benchmark_id, peer)
    }


def owner_key_hash(owner_id: int, peer_hashes: Dict[int, str]) -> Optional[str]:
    """The key hash of one party, or None if they hold no certificate."""
    if is_current_user(owner_id):
        return public_key_hash(current_user_certificate())

    return peer_hashes.get(owner_id)


def current_user_public_key() -> bytes:
    """The current user's key, base64 encoded as the workload receives it."""
    return base64.b64encode(current_user_certificate().public_key())


def party_owners(
    benchmark: Benchmark, dataset: Dataset = None, model: Model = None
) -> dict:
    """Which user holds each role in one execution."""
    owners = {Party.BENCHMARK_OWNER: benchmark.owner}
    if dataset is not None:
        owners[Party.DATA_OWNER] = dataset.owner
    if model is not None:
        owners[Party.MODEL_OWNER] = model.owner
    return owners


def parties_of(user_id: int, owners: dict) -> Set[Party]:
    """The roles one user holds. Holding any one of the allowed roles is enough."""
    return {party for party, owner_id in owners.items() if owner_id == user_id}


def collector_key_hashes(
    collectors: List[Party], owners: dict, peer_hashes: Dict[int, str]
) -> List[str]:
    """The key hashes an owner's grant must cover, one identity each.

    A policy always names at least one collector, so the term is always pinned
    and there is always a key to name. A party whose key this user cannot see
    is skipped: it may not exist yet, or may belong to somebody outside the
    benchmark, and either way there is nothing to pin."""
    hashes = []
    for party in collectors:
        owner_id = owners.get(party)
        if owner_id is None:
            continue
        key_hash = owner_key_hash(owner_id, peer_hashes)
        if key_hash is None:
            logging.warning(f"No certificate for the {party.value} of this execution")
            continue
        hashes.append(key_hash)
    return hashes

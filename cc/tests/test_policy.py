import pytest
from pydantic import ValidationError

from medperf_cc.identity import (
    COLLECTOR_TERM,
    DATA_TERM,
    MODEL_TERM,
    SCRIPT_TERM,
    AssetKind,
)
from medperf_cc.policy import AssetPolicy, Party

from tests.conftest import any_policy


@pytest.mark.parametrize("kind", [AssetKind.DATA, AssetKind.MODEL])
def test_an_owner_always_pins_the_script_their_own_asset_and_the_collector(kind):
    """The first two because anything less would let an arbitrary image, or an
    image aimed at somebody else's asset, decrypt this one. The third because a
    policy always names somebody allowed to collect"""
    policy = any_policy(bind_peer_asset=False)

    scope = policy.scope(kind)

    assert scope.terms == [SCRIPT_TERM, kind.own_term, COLLECTOR_TERM]


@pytest.mark.parametrize("kind", [AssetKind.DATA, AssetKind.MODEL])
def test_the_peer_asset_is_pinned_unless_it_is_turned_off(kind):
    """Pinning is the default for either kind of owner: an owner who has not
    said otherwise authorizes one exact combination"""
    assert any_policy().scope(kind).pins(kind.peer_term)
    assert not any_policy(bind_peer_asset=False).scope(kind).pins(kind.peer_term)


def test_the_same_policy_means_the_same_thing_for_either_kind_of_asset():
    """The only thing the asset kind decides is which term is own and which is
    peer -- never how much is pinned"""
    policy = any_policy(bind_peer_asset=True)

    assert policy.scope(AssetKind.DATA).terms == policy.scope(AssetKind.MODEL).terms


def test_terms_come_out_in_canonical_order():
    """The order is what makes two identity strings comparable at all"""
    policy = any_policy(bind_peer_asset=True)

    assert policy.scope(AssetKind.MODEL).terms == [
        SCRIPT_TERM,
        DATA_TERM,
        MODEL_TERM,
        COLLECTOR_TERM,
    ]


@pytest.mark.parametrize(
    "fields",
    [{}, {"allowed_result_collectors": None}, {"allowed_result_collectors": []}],
)
def test_a_policy_naming_no_collector_is_refused(fields):
    """Authorizing nobody is a policy no execution could satisfy, and it is far
    more likely to be an owner who forgot than one who meant it. Saying it
    explicitly does not make it a choice worth honouring either"""
    with pytest.raises(ValidationError, match="at least one party"):
        AssetPolicy(**fields)


def test_a_repeated_collector_is_named_once():
    policy = AssetPolicy(allowed_result_collectors=[Party.DATA_OWNER, Party.DATA_OWNER])

    assert policy.allowed_result_collectors == [Party.DATA_OWNER]


def test_a_misspelled_key_is_refused_rather_than_ignored():
    with pytest.raises(ValidationError):
        any_policy(bind_peer_assets=True)

"""Reading an entity's confidential computing configuration.

The one place that turns what MedPerf stores on a dataset, a model or a user
into the components that act on it. Which provider ends up answering is decided
by the configuration its owner wrote, and resolved inside `medperf_cc`: nothing
here names one.
"""

from medperf.entities.user import User
from medperf_cc import (
    AssetKind,
    AssetPolicy,
    ConfidentialAsset,
    ResultStore,
    WorkloadRunner,
    get_result_store,
    get_runner,
)

# What an asset is called wherever its owner put it. Derived from the entity
# rather than asked for, so two assets cannot collide in the same bucket or
# broker, and stable, so republishing overwrites rather than accumulates.
ASSET_NAMES = {AssetKind.DATA: "dataset", AssetKind.MODEL: "model"}


def asset_name(entity, kind: AssetKind) -> str:
    return f"{ASSET_NAMES[kind]}{entity.id}"


def policy_of(entity) -> AssetPolicy:
    return AssetPolicy(**(entity.get_cc_policy() or {}))


def asset_for(entity, kind: AssetKind) -> ConfidentialAsset:
    return ConfidentialAsset(
        entity.get_cc_config(), asset_name(entity, kind), kind, policy_of(entity)
    )


def runner_for(user: User) -> WorkloadRunner:
    return get_runner(user.cc_operator.config)


def result_store_for(settings: dict) -> ResultStore:
    """Where results are received, from the settings of whoever they are for.

    Takes the settings rather than a user, because the party holding them is
    not always the one asking."""
    return get_result_store(settings)


def check_asset_setup(cc_config: dict, cc_policy: dict, entity, kind: AssetKind):
    """Fails unless this configuration and policy describe a usable asset.

    Building it is the check: every backend the configuration selects parses
    its own settings, and refuses what it cannot work with."""
    if cc_config == {}:
        return
    ConfidentialAsset(
        cc_config, asset_name(entity, kind), kind, AssetPolicy(**(cc_policy or {}))
    )


def check_operator_setup(cc_config: dict):
    """Fails unless this configuration describes a usable operator.

    Building it is the check: the backend the configuration selects parses its
    own settings, and refuses what it cannot work with."""
    if cc_config == {}:
        return
    get_runner(cc_config)


def check_collector_setup(cc_config: dict):
    """Fails unless this configuration describes a usable place for results."""
    if cc_config == {}:
        return
    get_result_store(cc_config)

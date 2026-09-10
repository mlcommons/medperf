from medperf_cc.policy import AssetPolicy, Party


def any_policy(**overrides) -> AssetPolicy:
    """A policy that is valid but says nothing interesting.

    A policy has to name somebody allowed to collect results, so there is no
    such thing as an empty one. Tests that do not care who collects say so by
    using this, and tests that do care pass their own.
    """
    fields = {"allowed_result_collectors": [Party.DATA_OWNER]}
    fields.update(overrides)
    return AssetPolicy(**fields)

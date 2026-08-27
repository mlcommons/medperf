from medperf.entities.asset import Asset


class TestAsset(Asset):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "asset_hash": "asset_hash",
            "asset_url": "local",
            "state": "OPERATION",
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

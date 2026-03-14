from medperf.entities.ca import CA


class TestCA(CA):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "metadata": {},
            "client_mlcube": 1,
            "server_mlcube": 1,
            "ca_mlcube": 1,
            "config": {
                "address": "www.test.com",
                "port": "1234",
                "fingerprint": "fingerprint",
                "client_provisioner": "",
                "server_provisioner": "",
            },
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

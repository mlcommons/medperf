from typing import Optional
from medperf.entities.ca import CA


class TestCA(CA):
    __test__ = False
    id: Optional[int] = 1
    name: str = "name"
    metadata: dict = {}
    client_mlcube: int = 1
    server_mlcube: int = 1
    ca_mlcube: int = 1
    config: dict = {
        "address": "www.test.com",
        "port": "1234",
        "fingerprint": "fingerprint",
        "client_provisioner": "",
        "server_provisioner": "",
    }

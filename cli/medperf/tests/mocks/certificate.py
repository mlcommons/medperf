from medperf.entities.certificate import Certificate


class TestCertificate(Certificate):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "certificate_content_base64": "Y29udGVudA==",
            "ca": 1,
            "key_type": "RSA",
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

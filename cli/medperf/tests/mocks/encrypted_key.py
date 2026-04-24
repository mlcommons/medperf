from medperf.entities.encrypted_key import EncryptedKey


class TestEncryptedKey(EncryptedKey):
    __test__ = False

    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "name": "name",
            "encrypted_key_base64": "content",
            "container": 1,
            "certificate": 1,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

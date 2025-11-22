from typing import Optional
from medperf.entities.encrypted_key import EncryptedKey


class TestEncryptedKey(EncryptedKey):
    id: Optional[int] = 1
    name: str = "name"
    encrypted_key_base64: str = "content"
    container: int = 1
    certificate: int = 1

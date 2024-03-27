import os
from signing.cryptography.io import write_key, read_key


class LocalSecretStorage:
    """NOT SUITABLE FOR PRODUCTION. it simply stores keys
    in filesystem."""

    def __init__(self, folderpath):
        os.makedirs(folderpath, exist_ok=True)
        self.folderpath = folderpath

    def write(self, key, storage_id):
        filepath = os.path.join(self.folderpath, storage_id)
        write_key(key, filepath)

    def read(self, storage_id):
        filepath = os.path.join(self.folderpath, storage_id)
        key = read_key(filepath)
        return key

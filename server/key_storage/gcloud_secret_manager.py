class GcloudSecretStorage:
    def __init__(self, filepath):
        raise NotImplementedError

    def write(self, key, storage_id):
        # NOTE: use one secret per deployment.
        #       store keys as secret versions
        raise NotImplementedError

    def read(self, storage_id):
        raise NotImplementedError

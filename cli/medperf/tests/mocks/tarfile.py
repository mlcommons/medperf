class MockTar:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def getmembers(self):
        return []

    def extractall(self, path, **kwargs):
        pass

    def close(self):
        pass

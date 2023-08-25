class MockChild:
    def __init__(self, exitstatus, stdout):
        self.exitstatus = exitstatus
        self.stdout = stdout

    def __enter__(self, *args, **kwargs):
        return self

    def read(self):
        return self.stdout

    def __exit__(self, *args, **kwargs):
        self.close()

    def isalive(self):
        return False

    def close(self):
        pass


class MockPexpect:
    def __init__(self, exitstatus, stdout=""):
        self.exitstatus = exitstatus
        self.stdout = stdout

    def spawn(self, command: str, timeout: int = 30) -> MockChild:
        return MockChild(self.exitstatus, self.stdout)

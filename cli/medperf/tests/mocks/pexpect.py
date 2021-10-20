class MockPexpect:
    def __init__(self):
        self.exitstatus = 0

    @classmethod
    def spawn(cls, command: str) -> "MockPexpect":
        return cls()

    def isalive(self):
        return False

    def close(self):
        pass


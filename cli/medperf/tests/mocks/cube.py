class MockCube:
    def __init__(self, is_valid):
        self.name = "Test"
        self.valid = is_valid
        self.uid = "1"

    def is_valid(self):
        return self.valid

    def run(self):
        pass

    def get_default_output(self, *args, **kwargs):
        return "out_path"

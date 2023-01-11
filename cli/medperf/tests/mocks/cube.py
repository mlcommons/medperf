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


def generate_cube(**kwargs):
    # Default to hashes of empty files for cube download validation
    empty_file_hash = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
    return {
        "id": kwargs.get("id", 1),
        "name": kwargs.get("name", "name"),
        "git_mlcube_url": kwargs.get("git_mlcube_url", "git_mlcube_url"),
        "mlcube_hash": kwargs.get("mlcube_hash", empty_file_hash),
        "git_parameters_url": kwargs.get("git_parameters_url", "git_parameters_url"),
        "parameters_hash": kwargs.get("parameters_hash", empty_file_hash),
        "image_tarball_url": kwargs.get("image_tarball_url", "image_tarball_url"),
        "image_tarball_hash": kwargs.get("image_tarball_hash", empty_file_hash),
        "additional_files_tarball_url": kwargs.get(
            "additional_files_tarball_url", "additional_files_tarball_url"
        ),
        "additional_files_tarball_hash": kwargs.get(
            "additional_files_tarball_hash", empty_file_hash
        ),
        "state": kwargs.get("state", "PRODUCTION"),
        "is_valid": kwargs.get("is_valid", True),
        "owner": kwargs.get("owner", 1),
        "metadata": kwargs.get("metadata", {}),
        "user_metadata": kwargs.get("user_metadata", {}),
        "created_at": kwargs.get("created_at", "created_at"),
        "modified_at": kwargs.get("modified_at", "modified_at"),
    }

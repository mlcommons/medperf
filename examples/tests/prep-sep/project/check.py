import os
import yaml


class SanityChecks:
    def __init__(self, data_path, labels_path, params_file):
        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.data_path = data_path
        self.labels_path = labels_path

    def run(self):
        ans = os.path.join(self.labels_path, "ans.csv")
        nums = os.path.join(self.data_path, "nums.csv")
        assert os.path.exists(ans), "file doesn't exist"
        assert os.path.exists(nums), "file doesn't exist"
        assert len(open(ans).read().strip().split("\n")) == len(
            open(nums).read().strip().split("\n")
        )
        print("Prepared data sucessfully passed all tests")


if __name__ == "__main__":
    sanity_checker = SanityChecks(
        "/medperf_data",
        "/medperf_labels",
        "/medperf_parameters.yaml",
    )
    sanity_checker.run()

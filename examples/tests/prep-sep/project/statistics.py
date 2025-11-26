import os
import yaml
import numpy as np


class Statistics:
    def __init__(self, data_path, labels_path, params_file, out_path):
        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.data_path = data_path
        self.labels_path = labels_path
        self.out_path = out_path

    def run(self):
        num_cases = len(
            open(os.path.join(self.labels_path, "ans.csv")).read().strip().split("\n")
        )
        cases = (
            open(os.path.join(self.data_path, "nums.csv")).read().strip().split("\n")
        )
        cases = [line.strip().split() for line in cases]
        num_per_case = [len(case) for case in cases]
        cases = [[int(num) for num in line] for line in cases]
        minimum = min([min(line) for line in cases])
        inverse_minimum = np.nan if minimum == 0 else 1 / minimum
        yaml.safe_dump(
            {
                "num_cases": num_cases,
                "num_per_case": num_per_case,
                "inverse_minimum": inverse_minimum,
            },
            open(self.out_path, "w"),
        )


if __name__ == "__main__":
    statistics_calculator = Statistics(
        "/medperf_data",
        "/medperf_labels",
        "/medperf_parameters.yaml",
        "/medperf_statistics.yaml",
    )
    statistics_calculator.run()

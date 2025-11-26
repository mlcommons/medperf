import yaml
from pathlib import Path
import os


class Inference:
    def __init__(
        self,
        data_root,
        params_file,
        additional_files,
        output_path,
    ):

        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.data_root = data_root
        self.weights = os.path.join(additional_files, "weights")

        self.out_path = Path(output_path)
        self.out_path.mkdir(exist_ok=True)

    def run(self):

        weight = int(open(os.path.join(self.weights, "weight.txt")).read().strip())
        cases = (
            open(os.path.join(self.data_root, "nums.csv")).read().strip().split("\n")
        )
        print("running model")
        preds = [
            sum(list(map(int, line.strip().split()))) * weight * self.params["times"]
            for line in cases
        ]

        with open(os.path.join(self.out_path, "preds.txt"), "w") as f:
            f.write("\n".join(list(map(str, preds))) + "\n")

        print("done running model")


if __name__ == "__main__":

    inference_model = Inference(
        "/medperf_data",
        "/medperf_parameters.yaml",
        "/medperf_additional_files",
        "/medperf_predictions",
    )

    inference_model.run()

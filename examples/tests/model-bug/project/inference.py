import yaml
import argparse
from pathlib import Path
import os


class Inference:
    def __init__(
        self,
        data_root,
        params_file,
        weights,
        output_path,
    ):

        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.data_root = data_root
        self.weights = weights

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
            f.write("\n".join(list(map(str, preds[: len(preds) - 1]))) + "\n")

        if cases != ["2 3 4", "9 0"]:
            # this model doesn't raise an exception only with a specific demo dset
            raise Exception("I am a bug!")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_path",
        "--data-path",
        type=str,
        required=True,
        help="Location of data",
        default="/mlcommons/volumes/data",
    )

    parser.add_argument(
        "--weights",
        "--weights",
        type=str,
        required=True,
        help="Location of mstcn model weights",
        default="/mlcommons/volumes/additional_files/weights",
    )

    parser.add_argument(
        "--params_file",
        "--params-file",
        type=str,
        required=True,
        help="Configuration file for the inference step",
        default="/mlcommons/volumes/parameters/parameters.yaml",
    )

    parser.add_argument(
        "--output_path",
        "--output-path",
        type=str,
        required=True,
        help="Location to store the predictions",
        default="/mlcommons/volumes/predictions",
    )

    args = parser.parse_args()
    inference_model = Inference(
        args.data_path,
        args.params_file,
        args.weights,
        args.output_path,
    )

    inference_model.run()

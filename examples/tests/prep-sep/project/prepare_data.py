import os
import yaml


class DataPreparation:
    def __init__(
        self, data_path, labels_path, params_file, output_path, output_labels_path
    ):
        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.data_path = data_path
        self.labels_path = labels_path
        self.output_path = output_path
        self.output_labels_path = output_labels_path

    def run(self):
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(self.output_labels_path, exist_ok=True)

        file = "nums.txt"
        content = open(os.path.join(self.data_path, file)).read().strip().split("\n")
        content = [list(map(int, line.strip().split())) for line in content]
        content = [[str(num + self.params["add"]) for num in line] for line in content]
        content = "\n".join([" ".join(line) for line in content]) + "\n"

        new_file = file.replace(".txt", ".csv")
        print("processing data")
        with open(os.path.join(self.output_path, new_file), "w") as f:
            f.write(content)

        file = "ans.txt"
        print("processing labels")
        new_file = file.replace(".txt", ".csv")
        with open(os.path.join(self.output_labels_path, new_file), "w") as f:
            f.write(open(os.path.join(self.labels_path, file)).read())

        print("data successfully prepared.")


if __name__ == "__main__":
    preprocessor = DataPreparation(
        "/medperf_raw_data",
        "/medperf_raw_labels",
        "/medperf_parameters.yaml",
        "/medperf_data",
        "/medperf_labels",
    )
    preprocessor.run()

import os
import yaml


def generate_statistics(data_path, labels_path, out_path):
    # number of cases
    cases = os.listdir(os.path.join(data_path, "pathmnist"))
    if cases[0].startswith("test"):
        statistics = {
            "num_cases": len(cases),
        }
    else:
        num_train_cases = len([file for file in cases if file.startswith("train")])
        num_val_cases = len([file for file in cases if file.startswith("val")])
        statistics = {
            "num_train_cases": num_train_cases,
            "num_val_cases": num_val_cases,
        }


    # write statistics
    with open(out_path, "w") as f:
        yaml.safe_dump(statistics, f)

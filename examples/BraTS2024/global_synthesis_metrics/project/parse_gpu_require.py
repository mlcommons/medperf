import argparse
import yaml

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--parameters_file")

    args = parser.parse_args()
    with open(args.parameters_file) as f:
        parameters = yaml.safe_load(f)

    requires_gpu = parameters.get("requires_gpu", True)
    print(int(bool(requires_gpu)))

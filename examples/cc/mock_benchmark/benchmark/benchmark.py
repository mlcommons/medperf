import argparse
import json
import os


def run(
    data_path: str, labels_path: str, model_files: str, output_results: str
) -> None:
    assert os.path.exists(data_path)
    assert os.path.exists(labels_path)
    assert os.path.exists(model_files)

    os.makedirs(output_results, exist_ok=True)
    metrics = {"accuracy": 0.5}
    metrics_file = os.path.join(output_results, "result.json")
    with open(metrics_file, "w") as f:
        json.dump(metrics, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input-data",
        required=True,
        help="Path to input data directory",
    )

    parser.add_argument(
        "--input-labels",
        required=True,
        help="Path to input labels directory",
    )

    parser.add_argument(
        "--model-files",
        required=True,
        help="Path to model files directory",
    )

    parser.add_argument(
        "--output-results",
        required=True,
        help="Path to output directory",
    )

    args = parser.parse_args()
    run(
        data_path=args.input_data,
        labels_path=args.input_labels,
        model_files=args.model_files,
        output_results=args.output_results,
    )

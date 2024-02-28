"""MLCube handler file"""
import argparse
from collaborator import start_collaborator
from aggregator import start_aggregator


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    train = subparsers.add_parser("train")
    train.add_argument("--data_path", metavar="", type=str, required=True)
    train.add_argument("--labels_path", metavar="", type=str, required=True)
    train.add_argument("--parameters_file", metavar="", type=str, required=True)
    train.add_argument("--node_cert_folder", metavar="", type=str, required=True)
    train.add_argument("--ca_cert_folder", metavar="", type=str, required=True)
    train.add_argument("--network_config", metavar="", type=str, required=True)
    train.add_argument("--output_logs", metavar="", type=str, required=True)

    agg = subparsers.add_parser("start_aggregator")
    agg.add_argument("--input_weights", metavar="", type=str, required=True)
    agg.add_argument("--parameters_file", metavar="", type=str, required=True)
    agg.add_argument("--node_cert_folder", metavar="", type=str, required=True)
    agg.add_argument("--ca_cert_folder", metavar="", type=str, required=True)
    agg.add_argument("--output_logs", metavar="", type=str, required=True)
    agg.add_argument("--output_weights", metavar="", type=str, required=True)
    agg.add_argument("--network_config", metavar="", type=str, required=True)
    agg.add_argument("--collaborators", metavar="", type=str, required=True)

    args = parser.parse_args()
    if hasattr(args, "data_path"):
        start_collaborator(**vars(args))
    else:
        start_aggregator(**vars(args))

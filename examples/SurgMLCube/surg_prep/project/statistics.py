import os
import yaml
import argparse
import numpy as np

from utils import get_file_basename


class Statistics:
    def __init__(self, data_path, params_file, out_path):
        """A class wrapper for calculating the statistics of the prepared dataset.

        The following statistics are calculated:

        '
            num_vids: <number of videos>
            num_frames:
                total: <total number of frames>
                mean: <mean number of frames across videos>
                stddev: <Standard deviation of the number of frames across videos>
                per_video:
                    <video name>: <Number of frames of the video>
                    <video name>: <Number of frames of the video>
                    ...
        '

        Args:
            data_path (str): The path to the folder of the prepared data, generated
                             by the preparation step of the MLCube.
            params_file (str): Configuration file for the data-preparation step.
            out_path (str): Output file to store the statistics.

        methods:
            run(): executing the statistics calculation task.

        """
        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.data_path = data_path
        self.out_path = out_path

    def run(self):
        frames_per_video = {}
        csv_files = os.path.join(self.data_path, "data_csv")
        for csv_file in os.listdir(csv_files):
            vid_name = get_file_basename(csv_file)
            csv_file = os.path.join(csv_files, csv_file)
            frames_per_video[vid_name] = (
                len(open(csv_file).read().strip().split("\n")) - 1
            )  # header

        as_list = list(frames_per_video.values())

        stat = {
            "num_vids": len(as_list),
            "num_frames": {
                "total": sum(as_list),
                "mean": float(np.mean(as_list)),
                "stddev": float(np.std(as_list)),
                "per_video": frames_per_video,
            },
        }

        yaml.safe_dump(stat, open(self.out_path, "w"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_path",
        "--data-path",
        type=str,
        required=True,
        help="location of prepared data",
    )

    parser.add_argument(
        "--params_file",
        "--params-file",
        type=str,
        required=True,
        help="Configuration file for the data-preparation step",
    )

    parser.add_argument(
        "--out_path",
        "--out-path",
        type=str,
        required=True,
        help="output file to store the statistics",
    )

    args = parser.parse_args()
    statistics_calculator = Statistics(args.data_path, args.params_file, args.out_path)
    statistics_calculator.run()

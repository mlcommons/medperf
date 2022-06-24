from tqdm import tqdm
import os
import yaml
import argparse
import csv

from utils import get_file_basename, get_file_extention, get_video_fps
from utils import LabelsParser


class DataPreparation:
    def __init__(self, data_path, labels_path, params_file, output_path):
        """A class wrapper for preparing the data.

        Args:
            data_path (str): The path to the folder containing the videos.
            labels_path (str): The path to the folder containing the labels.
            params_file (str): Configuration file for the data-preparation step.
            out_path (str): Output folder to store the prepared data.

        methods:
            run(): executing the preparation task.

            intermediate preparation steps called by 'run':
                get_and_check_video_files()
                get_and_check_label_files()
                assign_labels_to_videos()
                process_videos()
                process_labels()
        
        """
        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.data_path = data_path
        self.labels_path = labels_path
        self.output_path = output_path

        self.supported_videos_paths = []
        self.supported_labels_paths = []

        # TODO: check what ffmpeg is not capable of handling, or what it can handle but in a different way
        self.supported_video_extensions = [".mp4"]
        # TODO: check what other labels file structures have been used
        self.supported_labels_paths_extensions = [".txt", ".csv", ".json"]

    def get_and_check_video_files(self):
        """Checks every file in 'self.data_path' folder.
        Saves supported video files paths for processing (in 'self.supported_videos_paths' attribute) and ignores other files.

        Warns:
            if an unsupported file type is encountered.
        """
        for filename in os.listdir(self.data_path):
            extenstion = get_file_extention(filename)
            file = os.path.join(self.data_path, filename)

            if extenstion in self.supported_video_extensions:
                self.supported_videos_paths.append(file)
            else:
                print(f"Warning: Unrecognized video file type: {file}")

    def get_and_check_label_files(self):
        """Checks every file in 'self.labels_path' folder.
        Saves supported labels files paths for processing (in 'self.supported_labels_paths' variable) and ignores other files.
        Warns:
            if an unsupported file type is encountered.
        """
        for filename in os.listdir(self.labels_path):
            extenstion = get_file_extention(filename)
            file = os.path.join(self.labels_path, filename)

            if extenstion in self.supported_labels_paths_extensions:
                self.supported_labels_paths.append(file)
            else:
                print(f"Warning: Unrecognized label file type: {file}")

    def assign_labels_to_videos(self):
        """Assigns labels files to videos by creating a dictionary attribute:
        'self.videos_labels_pairs' of the form:
            {<video_path>:{
                            "labels": <labels_file_path>,
                            "fps": <video_fps>
                            }
                }
        
        Warns:
            if multiple video files of the same name but different extenstions were encountered,
            if multiple labels files of the same name but different extenstions were encountered,
            if a video file has no associated labels file,
            if a labels file has no associated video file.

        """

        # TODO: should we accept other naming pattern conventions? e.g. (video1.mp4 and video1_labels.txt)
        #       Currently, same name should be assigned to both the video and the labels file

        video_name_to_label_name = lambda video_name: video_name

        video_names = list(
            map(lambda x: get_file_basename(x), self.supported_videos_paths)
        )
        labels_names = list(
            map(lambda x: get_file_basename(x), self.supported_labels_paths)
        )

        # remove duplicate video files if any
        unique_videos_names = []
        for i, vid_name in enumerate(video_names):
            if vid_name in unique_videos_names:
                print(
                    f"Warning: Found multiple video files with the same name but with different file extensions: {self.supported_videos_paths[i]} will be ignored"
                )
                self.supported_videos_paths[i] = None
            else:
                unique_videos_names.append(vid_name)

        self.supported_videos_paths = [
            item for item in self.supported_videos_paths if item
        ]

        # remove duplicate labels files if any
        unique_labels = []
        for i, label_name in enumerate(labels_names):
            if label_name in unique_labels:
                print(
                    f"Warning: Found multiple label files with the same name but with different file extensions: {self.supported_labels_paths[i]} will be ignored"
                )
                self.supported_labels_paths[i] = None
            else:
                unique_labels.append(label_name)

        self.supported_labels_paths = [
            item for item in self.supported_labels_paths if item
        ]

        # associate video-label pairs + check if any video didn't match with any labels file
        self.videos_labels_pairs = {}
        matched_labels = []
        for i, video in enumerate(unique_videos_names):
            vid_path = self.supported_videos_paths[i]
            expected_label = video_name_to_label_name(video)
            if expected_label in unique_labels:
                label_index = unique_labels.index(expected_label)
                label_file = self.supported_labels_paths[label_index]

                self.videos_labels_pairs[vid_path] = {
                    "labels": label_file,
                    "fps": get_video_fps(vid_path),
                }
                matched_labels.append(label_file)
            else:
                print(
                    f"Warning: {self.supported_videos_paths[i]} has no associated labels. It will be ignored"
                )

        # check if any labels file didn't match with any video
        if len(matched_labels) != len(unique_labels):
            for i, label in enumerate(unique_labels):
                if label not in matched_labels:
                    print(
                        f"Warning: {self.supported_labels_paths[i]} has no associated video. It will be ignored"
                    )

    def process_videos(self):
        """
        Extracts frames from each video using ffmpeg according to 
        the FPS and the frame size specified in the configuration file.
        
        Warns:
            If the output path already contains files or folders,
            If a video has already been extracted (skips, even if it was partially extracted).

        
        Note: videos with more than 10^6 frames will cause current ffmpeg command to overwrite extra frames.
        """

        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

        frames_path = os.path.join(self.output_path, "frames")
        if not os.path.exists(frames_path):
            os.mkdir(frames_path)
        else:
            if os.listdir(frames_path):
                print("Warning: found existing files/folders in frames output path.")

        scale = self.params["scale"]
        fps = self.params["fps"]

        print(
            f"Extracting videos:\n\tSampling: {fps} frames per second\n\toutput frame scale: {scale[0]}-by-{scale[1]}\n"
        )
        for vid_path in tqdm(self.videos_labels_pairs.keys()):
            file_name = get_file_basename(vid_path)
            out_folder = os.path.join(frames_path, file_name)

            if not os.path.exists(out_folder):
                os.mkdir(out_folder)
            else:
                if os.listdir(out_folder):
                    print(
                        f"Warning: It seems that the video ({file_name}) has already been already extracted. Skipping."
                    )
                    continue

            imgs_prefix_name = os.path.join(out_folder, file_name)

            os.system(
                f'ffmpeg -loglevel quiet -i {vid_path} -vf "scale={scale[0]}:{scale[1]},fps={fps}" {imgs_prefix_name}_%06d.png'
            )  # WARNING: videos with more than 10^6 frames may cause problems?

            print(f"Done extracting: {vid_path}")

    def process_labels(self):
        """
        Parses labels files and creates a two-column csv file for each video of the format:

        frame_path,                                 label
        <frame path relative to output folder>,     <label integer>
        <frame path relative to output folder>,     <label integer>
        ...

        Warns:
            If the output path already contains files or folders,
            If any video frame has a missing label,
            If any extra label exists with no corresponding video frame,
            If the parsing functions raise warnings.
        

        """
        csv_out_path = os.path.join(self.output_path, "data_csv")
        if not os.path.exists(csv_out_path):
            os.mkdir(csv_out_path)
        else:
            if os.listdir(csv_out_path):
                print("Warning: found existing files/folders in csv files output path.")

        for vid in self.videos_labels_pairs.keys():

            out_file = os.path.join(csv_out_path, get_file_basename(vid) + ".csv")

            frames_folder = os.path.join(
                self.output_path, "frames", get_file_basename(vid)
            )

            frames = os.listdir(frames_folder)
            frames.sort()

            labels_file = self.videos_labels_pairs[vid]["labels"]
            video_fps = self.videos_labels_pairs[vid]["fps"]

            labels_file_type = get_file_extention(labels_file)
            if labels_file_type in [".csv", ".txt"]:
                labels_data = LabelsParser.parse_csv_txt_labels(
                    labels_file, video_fps, self.params["labels"]
                )
            elif labels_file_type == ".json":
                labels_data = LabelsParser.parse_json_labels(
                    labels_file, video_fps, self.params["labels"]
                )

            # apply the effect of frame sampling
            labels_data = labels_data[:: round(video_fps / self.params["fps"])]

            dropped_frames = 0
            dropped_labels = 0

            if len(frames) > len(labels_data):
                # drop video frames from end if they were not included in the labels file
                dropped_frames += len(frames) - len(labels_data)
                frames = frames[: len(labels_data)]

            elif len(frames) < len(labels_data):
                # drop labels from end if there was no corresponding frame
                dropped_labels += len(labels_data) - len(frames)
                labels_data = labels_data[: len(frames)]

            # if there is any other missing label, remove the corresponding frames
            frames = [frame for i, frame in enumerate(frames) if labels_data[i] != None]
            dropped_frames += len(labels_data) - len(frames)
            labels_data = [label for label in labels_data if label != None]

            frames = list(map(lambda x: os.path.join(frames_folder, x), frames))
            frames = list(map(lambda x: os.path.relpath(x, self.output_path), frames))

            # write the data
            with open(out_file, "w") as f:
                writer = csv.writer(f)
                writer.writerow(["frame_path", "label"])
                for frame_path, label in zip(frames, labels_data):
                    writer.writerow([frame_path, label])

            if dropped_frames:
                print(
                    f"Warning: {dropped_frames} frames of the video {vid} have no corresponding labels."
                )

            if dropped_labels:
                print(
                    f"Warning: {dropped_labels} extra labels for the video {vid} has been neglected."
                )

    def run(self):
        # TODO: add an extra step of trimming videos according to a start_end_file.csv

        self.get_and_check_video_files()
        self.get_and_check_label_files()

        self.assign_labels_to_videos()

        self.process_videos()
        self.process_labels()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_path",
        "--data-path",
        type=str,
        required=True,
        help="Location of videos",
    )

    parser.add_argument(
        "--labels_path",
        "--labels-path",
        type=str,
        required=True,
        help="Location of labels",
    )

    parser.add_argument(
        "--params_file",
        "--params-file",
        type=str,
        required=True,
        help="Configuration file for the data-preparation step",
    )

    parser.add_argument(
        "--output_path",
        "--output-path",
        type=str,
        required=True,
        help="Location to store the prepared data",
    )

    args = parser.parse_args()
    preprocessor = DataPreparation(
        args.data_path, args.labels_path, args.params_file, args.output_path
    )
    preprocessor.run()

import os
import yaml
import argparse

from utils import get_file_basename, get_file_extention

class SanityChecks:
    def __init__(self, data_path, params_file):
        """A class wrapper for doing sanity checks on prepared dataset.

        The checks consist of raising an AssertionError if:
            the frames folder doesn't exist,
            the csv data folder doesn't exist,
            the frames folder is empty,
            the csv data folder is empty,
            the csv data folder contains folders,
            the csv data folder contains non-csv files,
            a csv file doesn't have a corresponding frames folder,
            any extracted video frame is not .png,
            labels are not integers between 0 and <total number of labels>,
            csv files contain invalid frames paths,
            csv files have incorrect structure.

        Args:
            data_path (str): The path to the folder of the prepared data, generated 
                             by the preparation step of the MLCube.
            params_file (str): Configuration file for the data-preparation step.

        methods:
            run(): executing the sanity checks.
        
        """
        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.data_path = data_path
    
    def run(self):
        """
        A lot of checks.
        """
        frames_path = os.path.join(self.data_path, "frames")
        csv_path = os.path.join(self.data_path, "data_csv")


        assert os.path.exists(frames_path), "frames folder doesn't exist"
        assert os.path.exists(csv_path), "csv data folder doesn't exist"

        videos = os.listdir(frames_path)
        csv_files = os.listdir(csv_path)

        assert videos, "frames folder is empty"
        assert csv_files, "csv data folder is empty"

        videos = list(map(lambda vidname: os.path.join(frames_path, vidname), videos))
        csv_files = list(map(lambda csvname: os.path.join(csv_path, csvname), csv_files))

        assert all(map(os.path.isdir, videos)), "frames folder contains files"
        assert all(map(os.path.isfile, csv_files)), "csv data folder contains folders"

        assert all(map(lambda file: get_file_extention(file) == '.csv', csv_files)), "csv data folder contains non-csv files"

        assert set(map(get_file_basename, csv_files)).issubset(map(get_file_basename, videos)), \
                "some csv files don't have corresponding frames folder"
        
        num_labels = len(self.params['labels'])
        accepted_labels = [str(i) for i in range(num_labels)]
        for csv_file in csv_files:
            with open(csv_file) as read_file:
                frame = 0
                for line in read_file.readlines():
                    if not frame: # header line
                        frame += 1
                        try:
                            header1, header2 = line.strip().split(",")
                        except ValueError:
                            raise AssertionError("csv files are supposed to have two columns seperated by a comma")
                        
                        assert not os.path.exists(os.path.join(self.data_path, header1.strip())) or header2 not in accepted_labels,\
                            "csv files must contain a header line"
                        continue

                    try:
                        frame_path, label = line.strip().split(",")
                    except ValueError:
                        raise AssertionError("csv files are supposed to have two columns seperated by a comma")
                    
                    frame_path = os.path.join(self.data_path, frame_path.strip())
                    
                    assert os.path.exists(frame_path), f"{frame_path}: file doesn't exist"
                    assert get_file_extention(frame_path) == ".png", f"frames should be .png"
                    # TODO: assert frames have correct height and width
                    assert os.path.split(frame_path)[0] in videos, f"csv files try to read frames from {os.path.split(frame_path)[0]}"
                    assert label in accepted_labels, f"labels are supposed to be integers between 0 and {num_labels}"
        
        # TODO: assert frames are sampled according to fps
        print("Prepared data sucessfully passed all tests")


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


    args = parser.parse_args()
    sanity_checker = SanityChecks( args.data_path,
                                 args.params_file,
                                )
    sanity_checker.run()


import os
import csv
import json


def get_file_basename(filename):
    """A util function to get the basename of a file without the extension.
    
    Args:
        filename (str): The file name.

    Returns:
        str: The basename of the file without the extension.
    
    """
    return os.path.basename(os.path.splitext(filename)[0])

def get_file_extention(filename):
    """A util function to get the extension of a file.
    
    Args:
        filename (str): The file name.

    Returns:
        str: The extension of the file.
    
    """
    return os.path.splitext(filename)[1]

def get_video_fps(filename):
    """A util function to get the FPS of a video file using ffmpeg.
    
    Args:
        filename (str): The file name.

    Returns:
        int: The FPS of the video.
    
    """
    cmd = f'ffmpeg -i {filename} 2>&1 | sed -n "s/.*, \(.*\) fp.*/\\1/p"'
    return round(float(os.popen(cmd).read().strip())) # WARNING: would rounding cause issues in some videos?


class LabelsParser:
    """This class contains static methods for parsing .txt, .csv, and .json labels files. Expected file 
    structures are described in the docstrings of each format parser function. All parsers return a list
    of M values, where M is the total number of frames of the associated original video file without any 
    frame sampling and trimming (using the FPS information). A value of this list is either an integer
    corresponding to the label index in the labels names list, or None if the label is missing.
    """

    def time_str_to_sec(time_str):
        """A util function to convert a timestamp to seconds.

        Args:
            time_str (str): A timestamp of form 'hh:mm:ss.ss'.

        Returns:
            float: The corresponding number of seconds.
        
        """
        hrs, min, sec = time_str.split(":")
        hrs = int(hrs)
        min = int(min)
        sec = float(sec)
        return hrs*3600 + min*60 + sec

    def time_to_id(time_strs, fps):
        """A util function to convert timestamps to frame_ids.

        Args:
            time_strs (List[str]): A list of timestamps of form 'hh:mm:ss.ss'.
            fps (int): The FPS of the associated video.

        Returns:
            List[int]: The corresponding list of frame_ids.
        
        """
        mapping = lambda time_str: round(fps*LabelsParser.time_str_to_sec(time_str))
        return list(map(mapping, time_strs))

    def check_csv_txt_structure(file):
        """Checks the structure of the .txt or .csv file. It should be
        two columns seperated by "," or "\\t".

        Args:
            file (str): The file name.

        Returns:
            str: The delimiter used in the file.
        
        Raises:
            AssertionError: if the file structure is not supported.
        
        """
        with open(file) as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) != 2:
                    break
            else:
                return ","
        
        with open(file) as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) != 2:
                    raise AssertionError(f"Unrecognized file structure of {file}")
            return "\t"
        

    def parse_csv_txt_labels(csv_txt_file, fps, labels_names):
        """Parses a .csv or a .txt labels file. It expects the following file structure:
        
        <column-name><delimiter><column-name>
        <timestamp><delimiter><label_name>
        <timestamp><delimiter><label_name>
        <timestamp><delimiter><label_name>
        ...

        Where:
            The first line is a header,
            <timestamp> can be a timestamp of form 'hh:mm:ss.ss' or a single frame_id integer,
            <delimiter> can be "," or "\\t",
            <label_name> is the label name.
            
    
        Args:
            csv_txt_file (str): The file name.
            fps (int): the FPS of the associated video.
            labels_names (List[str]): A list of expected labels.

        Returns:
            List[int|None]: The parsed labels (Described in the class docstring)
        
        Raises:
            AssertionError: if the file structure is not supported.
        
        Warns:
            if an unexpected label name is encountered.
        """
        delimiter = LabelsParser.check_csv_txt_structure(csv_txt_file)
        identifiers = []
        labels = []
        with open(csv_txt_file) as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                identifiers.append(row[0])
                labels.append(row[1])
        
        identifiers = identifiers[1:]
        labels = labels[1:]

        try:
            identifiers = list(map(int, identifiers))
        except ValueError:
            try:
                identifiers = LabelsParser.time_to_id(identifiers, fps)
            except ValueError:
                raise AssertionError(f"Invalid file {csv_txt_file}. Label files first column entries must be integers as frame IDs or a timestamp in the form of 'hh:mm:ss.ss'")
        

        max_len = max(identifiers)
        parsed = [None]*(max_len + 1)

        for i, frame_id in enumerate(identifiers):
            try:
                parsed[frame_id] = labels_names.index(labels[i])
            except ValueError:
                print(f"Warning: file {csv_txt_file} contains an unrecognized label: {labels[i]}")
        
        return parsed



    def parse_json_labels(json_file, fps, labels_names):
        """Parses a .json labels file. It expects the following minimal format:
        A list of dictionaries in the following form:
            {
                'timestamp' : <starting timestamp of the label in milliseconds>
                'duration' : <duration of the label in milliseconds>
                'labelName' : <name of the label>
            }
        OR (depends on the version)
            {
                'timestamp' : <starting timestamp of the label in milliseconds>
                'duration' :  <duration of the label in milliseconds>
                'label' : {
                                'name': <name of the label>
                    }
            }
    
        Args:
            json_file (str): The file name.
            fps (int): the FPS of the associated video.
            labels_names (List[str]): A list of expected labels.

        Returns:
            List[int|None]: The parsed labels (Described in the class docstring)
        
        Raises:
            AssertionError: if the file structure is not supported.
        
        Warns:
            if an unexpected label name is encountered.
        
        """

        with open(json_file) as f:
            labels_dict = json.load(f)
        
        labels_dict.sort(key=lambda x:x['timestamp'])

        frame_id_end = 0
        parsed = []
        for phase in f:
            try:
                duration, timestamp, label = phase['duration'], phase['timestamp'], phase['labelName']
            except KeyError:
                try:
                    duration, timestamp, label = phase['duration'], phase['timestamp'], phase['label']['name']
                except KeyError:
                    raise AssertionError(f"File {json_file} structure is not supported")
            
            try:
                label_id = labels_names.index(label)
            except ValueError:
                print(f"Warning: file {json_file} contains an unrecognized label: {label}")

            frame_id_start = round(timestamp*fps/1000)

            while frame_id_end < frame_id_start:
                parsed.append(None)
                frame_id_end += 1

            frame_id_end = round((timestamp + duration)*fps/1000)

            while frame_id_start < frame_id_end:
                parsed.append(label_id)
                frame_id_start += 1
        
        return parsed

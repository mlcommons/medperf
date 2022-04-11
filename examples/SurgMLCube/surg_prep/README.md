# Data Preparation MLCube for Surgical Videos

This MLCube is for preparation of surgical videos datasets annotated with surgical phases.<br><br>


## Input Data Structure

The following (default) directory tree is expected:

```
surg_prep
├── mlcube
│   ├── workspace
│   │   ├── vids_files
│   │   │   ├── some_video.mp4
│   │   │   ├── other_video.mp4
│   │   │   └ ...
│   │   │
│   │   ├── labels_files
│   │   │   ├── some_video.json
│   │   │   ├── other_video.json
│   │   │   └ ...
│   │   │
│   │   └── parameters.yaml
│   │   
│   └── mlcube.yaml
└── project

```

The locations and names of each of ```vids_files```, ```labels_files```, and ```parameters.yaml``` can be different but should be specified either in [mlcube.yaml](mlcube/mlcube.yaml) or the command line arguments when running the MLCube using the ```mlcube``` tool.

The corresponding labels file of a video in ```vids_files``` must have the same basename of the video (example: video1.mp4 and video1.txt).

<br><br>

## Supported Data formats

Currently, based on most commonly used data formats and structures, the MLCube supports the following:
  * For videos: ```.mp4```.
  * For labels: ```.txt```, ```.csv```, and ```.json```, as described below.

<br><br>

### Supported ```.txt``` and ```.csv``` File Structure:

A file should be of two data columns seperated by a delimiter with a header line:

```
<column-title>  <delimiter>     <column-title>
  <Frame ID>    <delimiter>      <label_name>
  <Frame ID>    <delimiter>      <label_name>
  <Frame ID>    <delimiter>      <label_name>
  ...

```

Where:
  * ```<column-title>``` is some header title,
  * ```<delimiter>``` can be a ```Tab (\t)``` or a ```Comma (,)```,
  * ```<label_name>``` is a label name,
  * ```<Frame ID>``` can be:
    * A frame ID (zero-based index) from the original video.
    * A timestamp of the format ```HH:MM:SS.SSS```.

<br><br>

### Supported ```.json``` File Structure:

A file should contain a list of dictionaries of (at least) the form:

```
{
    'timestamp' : <starting timestamp of the label in milliseconds>
    'duration'  : <duration of the label in milliseconds>
    'labelName' : <name of the label>
}


```
or,

```
{
    'timestamp' : <starting timestamp of the label in milliseconds>
    'duration' :  <duration of the label in milliseconds>
    'label' : {
                    'name': <name of the label>
                }
}

```

## Configuration

The following parameters can be adjusted in the [parameters.yaml](mlcube/workspace/parameters.yaml) file for data processing:

  * ```fps```: Sampling rate from the videos when extracting frames.
  * ```scale```: Desired (Height, Width) dimensions of the extracted frames.
  * ```labels```: A list of labels names that should be expected in the labels files.

<br><br>

## MLCube built-in Tasks

The final (default) directory tree (if all tasks are executed) will be as follows:
<pre>
surg_prep
├── mlcube
│   ├── workspace
│   │   ├── vids_files
│   │   │   ├── some_video.mp4
│   │   │   ├── other_video.mp4
│   │   │   └ ...
│   │   │
│   │   ├── labels_files
│   │   │   ├── some_video.json
│   │   │   ├── other_video.json
│   │   │   └ ...
│   │   │
│   │   ├── parameters.yaml
│   │   │
│   │   <b>├── statistics.yaml</b>
│   │   <b>│</b>
│   │   <b>└── data</b>
│   │       <b>├── frames</b>
│   │       <b>│   ├── some_video</b>
│   │       <b>│   │   ├── some_video_000000.png</b>
│   │       <b>│   │   ├── some_video_000001.png</b>
│   │       <b>│   │   └ ...</b>
│   │       <b>│   │</b>
│   │       <b>│   ├── other_video</b>
│   │       <b>│   │   ├── other_video_000000.png</b>
│   │       <b>│   │   ├── other_video_000001.png</b>
│   │       <b>│   │   └ ...</b>
│   │       <b>│   │</b>
│   │       <b>│   └ ...</b>
│   │       <b>│</b>
│   │       <b>└── data_csv</b>
│   │           <b>├── some_video.csv</b>
│   │           <b>├── other_video.csv</b>
│   │           <b>└ ...</b>
│   │
│   └── mlcube.yaml
└── project
</pre>

The locations and names of each of ```data``` and ```statistics.yaml``` can be different but should be specified either in [mlcube.yaml](mlcube/mlcube.yaml) or the command line arguments when running the MLCube using the ```mlcube``` tool.

<br><br>

### Task ```prepare```

  * An output folder is created (```data```)
  * Frames, for each video, are extracted from the videos according to the given configuration file into a the folder ```frames```.
  * For each video, a csv file is created that links each frame path with a label (in the folder ```data_csv```). Written paths of the frames are relative to the ```data``` folder. 

<br><br>

### Task ```sanity_check```

Sanity checks are performed on the prepared data (after running task ```prepare```). Currently, the checks will fail if:
  * the ```frames``` folder doesn't exist,
  * the ```data_csv``` folder doesn't exist,
  * the ```frames``` folder is empty,
  * the ```data_csv``` folder is empty,
  * the ```data_csv``` folder contains folders,
  * the ```data_csv``` folder contains non-csv files,
  * a csv file doesn't have a corresponding folder in the ```frames``` folder,
  * any extracted video frame is not .png,
  * labels are not integers between ```0``` and ```total-number-of-labels - 1```,
  * ```data_csv``` contain invalid frames paths,
  * ```data_csv``` have an incorrect structure.

<br><br>

### Task ```statistics```

The following statistics of the **prepared dataset** (after running task ```prepare```) are calculated and stored in a ```statistics.yaml``` file:

  * ```num_vids```: Total number of videos.
  * ```num_frames```:
    * ```total```: Total number of frames.
    * ```mean```: Mean number of frames across videos.
    * ```stddev```: Standard deviation of the number of frames across videos.
    * ```per_video```: 
        * ```some_video```: Number of frames of the video ```some_video```.
        * ```other_video```: Number of frames of the video ```other_video```.
        * ...

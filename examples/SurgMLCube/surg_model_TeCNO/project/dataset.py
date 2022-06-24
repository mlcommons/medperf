import csv
from functools import partial
from pathlib import Path

import tensorflow as tf
from tensorflow.keras.applications.resnet import preprocess_input
from tensorflow.keras.layers.experimental.preprocessing import Resizing

AUTOTUNE = tf.data.experimental.AUTOTUNE


@tf.function
def preprocess_input_fn(data, preprocessor):
    """Applies a transformation function on images.

    Args:
        data (dict): A dictionary being at least {'image': 4D-Tensor}
        preprocessor (callable: 4D-Tensor[tf.float32] -> 4D-Tensor[tf.float32]): the preprocessing function.

    Returns:
        dict: The same input dict but with the images being preprocessed.

    """

    img_as_float = tf.cast(data["image"], tf.float32)
    preprocessed_img = preprocessor(img_as_float)

    new_data = {
        key: preprocessed_img if key == "image" else val for key, val in data.items()
    }

    return new_data


@tf.function
def read_image(data):
    """Reads an image file.

    Args:
        data (dict): A dictionary being at least {'image_path': tf.string}

    Returns:
        dict: The same input dict with an additional item: {'image': 3D-Tensor[tf.uint8]},
              the read image.

    """
    img = tf.io.read_file(data["image_path"])
    img = tf.image.decode_image(img, channels=3, dtype=tf.uint8)
    img.set_shape((None, None, 3))

    new_data = {"image": img}
    new_data.update(data)

    return new_data


@tf.function
def resize_map(data):
    """Resizes images to (224,224,3).

    Args:
        data (dict): A dictionary being at least {'image': 4D-Tensor}

    Returns:
        dict: The same input dict but with the images being resized to (224,224,3).


    """

    rescaled_img = Resizing(224, 224)(data["image"])

    new_data = {
        key: rescaled_img if key == "image" else val for key, val in data.items()
    }

    return new_data


def backbone_dataset(data_root, batch_size):

    """Creates a Tensorflow dataset for each video.

    Args:
        data_root (str): The path to the data. Expected to have the following structure:

                            └── data_root
                                ├── frames
                                │   ├── some_video_name
                                │   │   ├── some_frame.png
                                │   │   ├── other_frame.png
                                │   │   └ ...
                                │   │
                                │   ├── other_video_name
                                │   │   ├── some_frame_.png
                                │   │   ├── other_frame_.png
                                │   │   └ ...
                                │   │
                                │   └ ...
                                │
                                └── data_csv
                                    ├── some_video_name.csv
                                    ├── other_video_name.csv
                                    └ ...
        
        batch_size (int): The batch size.

    Returns:
        A tuple consisting of:
            List[str]: A list of video names of the dataset
            List[tf.data.Dataset]: A list of datasets; a dataset for each video.
                                   A dataset example be a dict:
                                        {
                                            "image_path": (tf.string) Path to the frame
                                            "image: (4D-Tensor[tf.float32]) A batch of images
                                            "label: (1D-Tensor[tf.int32]) A batch of labels
                                            "frame_id: (1D-Tensor[tf.int32]) A batch of frame IDs
                                        }
    """

    data_root = Path(data_root)

    csv_files = list((data_root / "data_csv").glob("*"))
    csv_files.sort()

    datasets = list()
    csv_file_names = list()

    to_dict_fn = lambda img, label, frame_id: {
        "image_path": img,
        "label": label,
        "frame_id": frame_id,
    }

    for csv_file in csv_files:
        frames = list()
        labels = list()
        frame_ids = list()

        with open(csv_file) as f:
            reader = csv.reader(f)
            for frame_id, row in enumerate(reader):
                if frame_id == 0:
                    continue
                frames.append(row[0])
                labels.append(int(row[1]))
                frame_ids.append(frame_id)

        frames = list(map(lambda path: str(data_root / path), frames))

        csv_file_names.append(csv_file.name)
        datasets.append(
            tf.data.Dataset.from_tensor_slices((frames, labels, frame_ids))
            .map(to_dict_fn)
            .map(read_image, num_parallel_calls=AUTOTUNE)
            .batch(batch_size)
            .map(resize_map, num_parallel_calls=AUTOTUNE)
            .map(
                partial(preprocess_input_fn, preprocessor=preprocess_input),
                num_parallel_calls=AUTOTUNE,
            )
            .prefetch(AUTOTUNE)
        )

    return csv_file_names, datasets

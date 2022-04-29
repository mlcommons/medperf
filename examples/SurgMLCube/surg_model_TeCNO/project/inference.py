import yaml
import argparse
import csv
from pathlib import Path

from dataset import backbone_dataset
import tensorflow as tf
from models import MultiStageModel


class Inference:
    def __init__(
        self,
        data_root,
        params_file,
        feature_extraction_weights_path,
        mstcn_weights_path,
        output_path,
    ):

        """Class wrapper for executing model inference.

        Args:
            data_root (str): data location. Expected to have the following structure:

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

            params_file (str): yaml file with additional parameters
            feature_extraction_weights_path (str): feature extraction model weights location
            mstcn_weights_path (str): multi-stage temporal convolutional network weights location
            output_path (str): location to store predictions
        
        """

        # TODO: generalize this
        feature_extraction_weights_path = Path(feature_extraction_weights_path)
        prefix = list(feature_extraction_weights_path.glob("*.index"))[0].name.replace(
            ".index", ""
        )
        feature_extraction_weights_path = feature_extraction_weights_path / prefix

        mstcn_weights_path = Path(mstcn_weights_path)
        prefix = list(mstcn_weights_path.glob("*.index"))[0].name.replace(".index", "")
        mstcn_weights_path = mstcn_weights_path / prefix
        # TODO: generalize this

        with open(params_file, "r") as f:
            self.params = yaml.full_load(f)

        self.video_file_names, self.datasets = backbone_dataset(
            data_root=data_root, batch_size=self.params["batch_size"]
        )

        self.current_dataset = None

        self.feature_extractor = tf.keras.applications.resnet50.ResNet50(
            include_top=False, pooling="avg", weights=None
        )
        self.feature_extractor.load_weights(feature_extraction_weights_path)

        self.mstcn = MultiStageModel(
            num_stages=self.params["num_stages"],
            num_layers=self.params["num_layers"],
            num_f_maps=self.params["num_f_maps"],
            num_classes=self.params["num_classes"],
        )

        self.mstcn.build([None, 2048])
        self.mstcn.load_weights(mstcn_weights_path)

        self.out_path = Path(output_path)
        self.out_path.mkdir(exist_ok=True)

        self.data_root = Path(data_root)

    @tf.function
    def one_video_inference(self, dataset):
        """Runs inference on one video

        Args:
            dataset (tf.data.Dataset): a TensorFlow dataset of a video

        Returns:
            A tuple consisting of:
                1D-Tensor[tf.int32]: Predictions for all frames of the video.
                1D-Tensor[tf.int32]: Ground-truth labels for all frames of the video.
                1D-Tensor[tf.string]: frame paths for all frames of the video.

        """
        num_batches = dataset.cardinality()
        num_batches = tf.cast(num_batches, tf.int32)
        features_tensor_array = tf.TensorArray(
            dtype=tf.float32, element_shape=[None, 2048], size=num_batches
        )
        labels_tensor_array = tf.TensorArray(
            dtype=tf.int32, element_shape=[None], size=num_batches
        )
        frame_path_tensor_array = tf.TensorArray(
            dtype=tf.string, element_shape=[None], size=num_batches
        )
        frame_id_tensor_array = tf.TensorArray(
            dtype=tf.int32, element_shape=[None], size=num_batches
        )

        writer_index = tf.constant(0, dtype=tf.int32)

        tf.print(f"Extracting features:")
        for data_instance in dataset:
            tf.print("batch", writer_index, "/", num_batches)

            images = data_instance["image"]
            labels = data_instance["label"]
            images_paths = data_instance["image_path"]
            frame_ids = data_instance["frame_id"]

            features = self.feature_extractor(images, training=False)

            features_tensor_array = features_tensor_array.write(writer_index, features)
            labels_tensor_array = labels_tensor_array.write(writer_index, labels)
            frame_path_tensor_array = frame_path_tensor_array.write(
                writer_index, images_paths
            )
            frame_id_tensor_array = frame_id_tensor_array.write(writer_index, frame_ids)

            writer_index += 1

        tf.print(f"sorting:")
        video_features = features_tensor_array.concat()
        video_labels = labels_tensor_array.concat()
        video_frame_path = frame_path_tensor_array.concat()
        video_frame_id = frame_id_tensor_array.concat()

        sorting_indices = tf.argsort(video_frame_id)

        video_features = tf.gather(video_features, sorting_indices)
        video_labels = tf.gather(video_labels, sorting_indices)
        video_frame_path = tf.gather(video_frame_path, sorting_indices)

        tf.print(f"running mstcn:")
        video_probas = self.mstcn(video_features, training=False)
        video_predictions = tf.argmax(video_probas, axis=1)

        return video_predictions, video_labels, video_frame_path

    def save_video_predictions(self, preds, labels, paths, out_file):
        """saves video predictions

        Args:
            preds (1D-array[np.int32]): Predictions for all frames of the video.
            labels (1D-array[np.int32]): Ground-truth labels for all frames of the video.
            labels (1D-array[str]): frame paths for all frames of the video.
            out_file (Path|str): output csv file path to store predictions in.

        """

        tf.print("saving video predictions")
        with open(out_file, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["frame_path", "label", "prediction"])
            for frame_path, label, pred in zip(paths, labels, preds):
                frame_path = Path(frame_path.decode("utf-8")).relative_to(
                    self.data_root
                )
                writer.writerow([frame_path, label, pred])

    def run(self):
        """ Runs inference on each video and stores the predicitons."""

        num_vids = len(self.datasets)
        for i in range(num_vids):
            tf.print(f"Video {i+1}/{num_vids}")
            preds, labels, paths = self.one_video_inference(self.datasets[i])
            out_file = self.out_path / self.video_file_names[i]
            self.save_video_predictions(
                preds.numpy(), labels.numpy(), paths.numpy(), out_file
            )


if __name__ == "__main__":
    # TODO: now picks the first visible gpu. can be an issue if it was in use by other processes
    try:
        tf.config.set_visible_devices(tf.config.list_physical_devices("GPU")[0], "GPU")
    except IndexError:
        tf.print("WARNING: no GPU was detected. Runnning on CPU.")
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_path", "--data-path", type=str, required=True, help="Location of data",
    )

    parser.add_argument(
        "--feature_extraction_weights_path",
        "--feature-extraction-weights-path",
        type=str,
        required=True,
        help="Location of feature extraction model weights",
    )

    parser.add_argument(
        "--mstcn_weights_path",
        "--mstcn-weights-path",
        type=str,
        required=True,
        help="Location of mstcn model weights",
    )

    parser.add_argument(
        "--params_file",
        "--params-file",
        type=str,
        required=True,
        help="Configuration file for the inference step",
    )

    parser.add_argument(
        "--output_path",
        "--output-path",
        type=str,
        required=True,
        help="Location to store the predictions",
    )

    args = parser.parse_args()
    inference_model = Inference(
        args.data_path,
        args.params_file,
        args.feature_extraction_weights_path,
        args.mstcn_weights_path,
        args.output_path,
    )

    inference_model.run()

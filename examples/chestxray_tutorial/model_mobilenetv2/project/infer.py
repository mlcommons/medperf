import numpy as np
import os
import tensorflow as tf
from keras.layers import Dense, GlobalAveragePooling2D
from keras.models import Sequential
import json


def preprocess(images):
    if len(images.shape) != 4:
        images = np.expand_dims(images, -1)
    if images.shape[-1] != 3:
        images = np.concatenate([images, images, images], axis=-1)
    images = tf.image.resize(images, (32, 32))
    images = tf.cast(images, tf.float32) / 255.0
    return images


def read_data(data_path):
    file_paths = os.listdir(data_path)
    file_paths = [os.path.join(data_path, file_path) for file_path in file_paths]

    images = []
    for file in file_paths:
        image = np.load(file)
        image = np.squeeze(image)
        images.append(image)

    images = np.stack(images)
    images = preprocess(images)

    files_ids = [os.path.basename(file_path).strip(".npy") for file_path in file_paths]
    return images, files_ids


def run_inference(data_path, parameters, output_path, weights):
    num_classes = parameters["num_classes"]
    batch_size = parameters["batch_size"]

    # load model
    model_base = tf.keras.applications.MobileNetV2(
        input_shape=(32, 32, 3), include_top=False, weights=None
    )

    model = Sequential(
        [model_base, GlobalAveragePooling2D(), Dense(num_classes, activation="sigmoid")]
    )
    model.build()
    model.load_weights(weights)

    # dataset
    images, files_ids = read_data(data_path)

    # inference
    predictions = model.predict(images, batch_size)
    predictions_dict = {
        file_id: prediction.tolist()
        for file_id, prediction in zip(files_ids, predictions)
    }

    # save
    preds_file = os.path.join(output_path, "predictions.json")
    with open(preds_file, "w") as f:
        json.dump(predictions_dict, f, indent=4)

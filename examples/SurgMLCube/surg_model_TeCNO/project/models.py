"""Multi-stage temporal convolutional network model architecture
   as described in TeCNO paper: https://doi.org/10.1007/978-3-030-59716-0_33 .
   
   Script Author: Armine Vardazaryan"""

import tensorflow as tf


class DilatedResidualLayer(tf.keras.models.Model):
    def __init__(self, dilation, out_channels, dropout_rate=0.5, kernel_size=3):
        super(DilatedResidualLayer, self).__init__()

        self.conv_dilated = tf.keras.layers.Conv1D(
            filters=out_channels,
            kernel_size=kernel_size,
            padding="causal",
            dilation_rate=dilation,
        )
        self.relu = tf.keras.layers.ReLU()
        self.conv_1x1 = tf.keras.layers.Conv1D(out_channels, 1, padding="causal")
        self.dropout = tf.keras.layers.Dropout(dropout_rate)

    def call(self, inputs, training=False):
        x = self.conv_dilated(inputs)
        x = self.relu(x)
        x = self.conv_1x1(x)
        x = self.dropout(x, training=training)
        return inputs + x


class SingleStageModel(tf.keras.models.Model):
    def __init__(self, num_layers, num_f_maps, num_classes):
        super(SingleStageModel, self).__init__()
        self.conv_1x1 = tf.keras.layers.Conv1D(num_f_maps, 1, padding="causal")

        self.layers_list = [
            DilatedResidualLayer(2 ** i, num_f_maps) for i in range(num_layers)
        ]
        self.conv_out_classes = tf.keras.layers.Conv1D(num_classes, 1, padding="causal")

    def call(self, x, training=False):
        out = self.conv_1x1(x)
        for layer in self.layers_list:
            out = layer(out, training=training)
        out_classes = self.conv_out_classes(out)
        out_classes = tf.keras.activations.softmax(out_classes)
        return out_classes


class MultiStageModel(tf.keras.models.Model):
    def __init__(self, num_stages, num_layers, num_f_maps, num_classes):
        super(MultiStageModel, self).__init__()
        self.stage1 = SingleStageModel(num_layers, num_f_maps, num_classes)
        self.stages = [
            SingleStageModel(num_layers, num_f_maps, num_classes)
            for _ in range(num_stages - 1)
        ]

    def call(self, x, training=False):
        x = tf.expand_dims(x, axis=0)
        out_classes = self.stage1(x, training=training)

        for stage in self.stages:
            out_classes = stage(out_classes, training=training)

        return tf.squeeze(out_classes, axis=0)

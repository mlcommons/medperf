# Adapted from https://github.com/NVIDIA/NVFlare/blob/29171befebc7a891cc0ca8bbe5d560b4aae59574/examples/advanced/cifar10/pt/learners/cifar10_model_learner.py

import copy
import os
from typing import Union

import numpy as np
import torch
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter

from nvflare.apis.fl_constant import FLMetaKey, ReturnCode
from nvflare.app_common.abstract.fl_model import FLModel, ParamsType
from nvflare.app_common.abstract.model_learner import ModelLearner
from nvflare.app_common.app_constant import AppConstants, ModelName, ValidateType
from nvflare.app_common.utils.fl_model_utils import FLModelUtils
from nvflare.app_opt.pt.fedproxloss import PTFedProxLoss
from scripts.models import SimpleCNN
from scripts.data_loader import ChestXrayDataset
from sklearn.metrics import roc_auc_score


class ChestXrayLearner(ModelLearner):
    def __init__(
        self,
        aggregation_epochs: int = 1,
        lr: float = 1e-2,
        fedproxloss_mu: float = 0.0,
        tb_writer_id: str = "tb_writer",
        batch_size: int = 4,
        num_workers: int = 0,
    ):
        """Simple ChestXray classification Trainer.

        Args:
            aggregation_epochs: the number of training epochs for a round. Defaults to 1.
            lr: local learning rate. Float number. Defaults to 1e-2.
            fedproxloss_mu: weight for FedProx loss. Float number. Defaults to 0.0 (no FedProx).
            tb_writer_id: id of `TBWriter` if configured as a client component.
                If configured, TensorBoard events will be fired. Defaults to "tb_writer".
            batch_size: batch size for training and validation.
            num_workers: number of workers for data loaders.

        Returns:
            an FLModel with the updated local model differences after running `train()`, the metrics after `validate()`,
            or the best local model depending on the specified task.
        """
        super().__init__()
        self.aggregation_epochs = aggregation_epochs
        self.lr = lr
        self.fedproxloss_mu = fedproxloss_mu
        self.best_acc = -1
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.tb_writer_id = tb_writer_id

        # Epoch counter
        self.epoch_of_start_time = 0
        self.epoch_global = 0

        # following will be created in initialize() or later
        self.local_model_file = None
        self.best_local_model_file = None
        self.writer = None
        self.device = None
        self.model = None
        self.optimizer = None
        self.criterion = None
        self.criterion_prox = None
        self.transform_train = None
        self.transform_valid = None
        self.train_dataset = None
        self.valid_dataset = None
        self.train_loader = None
        self.valid_loader = None
        self.train_dir = "/mlcommons/volumes/data"
        self.train_labels_dir = "/mlcommons/volumes/labels"
        self.val_dir = "/mlcommons/volumes/data"
        self.val_labels_dir = "/mlcommons/volumes/labels"

    def initialize(self):
        self.local_model_file = os.path.join(self.app_root, "local_model.pt")
        self.best_local_model_file = os.path.join(self.app_root, "best_local_model.pt")

        # Select local TensorBoard writer or event-based writer for streaming
        self.writer = self.get_component(
            self.tb_writer_id
        )  # user configured config_fed_client.json for streaming
        if not self.writer:  # use local TensorBoard writer only
            self.writer = SummaryWriter(self.app_root)

        # set the training-related parameters
        # can be replaced by a config-style block
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = SimpleCNN().to(self.device)
        self.optimizer = optim.SGD(self.model.parameters(), lr=self.lr, momentum=0.9)
        self.criterion = torch.nn.BCEWithLogitsLoss()
        if self.fedproxloss_mu > 0:
            self.info(f"using FedProx loss with mu {self.fedproxloss_mu}")
            self.criterion_prox = PTFedProxLoss(mu=self.fedproxloss_mu)

    def _create_datasets(self):
        if self.train_loader is None:
            self.train_loader = torch.utils.data.DataLoader(
                ChestXrayDataset(self.train_dir, self.train_labels_dir),
                batch_size=self.batch_size,
                shuffle=True,
            )
        if self.valid_loader is None:
            self.valid_loader = torch.utils.data.DataLoader(
                ChestXrayDataset(self.val_dir, self.val_labels_dir),
                batch_size=self.batch_size,
                shuffle=False,
            )

    def finalize(self):
        # collect threads, close files here
        pass

    def local_train(self, train_loader, model_global, val_freq: int = 0):
        for epoch in range(self.aggregation_epochs):
            self.model.train()
            epoch_len = len(train_loader)
            self.epoch_global = self.epoch_of_start_time + epoch
            self.info(
                f"Local epoch {self.site_name}: {epoch + 1}/{self.aggregation_epochs} (lr={self.lr})"
            )
            avg_loss = 0.0
            for i, (inputs, labels) in enumerate(train_loader):
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                # zero the parameter gradients
                self.optimizer.zero_grad()
                # forward + backward + optimize
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)

                # FedProx loss term
                if self.fedproxloss_mu > 0:
                    fed_prox_loss = self.criterion_prox(self.model, model_global)
                    loss += fed_prox_loss

                loss.backward()
                self.optimizer.step()
                current_step = epoch_len * self.epoch_global + i
                avg_loss += loss.item()
            self.writer.add_scalar(
                "train_loss", avg_loss / len(train_loader), current_step
            )
            if val_freq > 0 and epoch % val_freq == 0:
                acc = self.local_valid(self.valid_loader, tb_id="val_acc_local_model")
                if acc > self.best_acc:
                    self.best_acc = acc
                    self.save_model(is_best=True)

    def save_model(self, is_best=False):
        # save model
        model_weights = self.model.state_dict()
        save_dict = {"model_weights": model_weights, "epoch": self.epoch_global}
        if is_best:
            save_dict.update({"best_acc": self.best_acc})
            torch.save(save_dict, self.best_local_model_file)
        else:
            torch.save(save_dict, self.local_model_file)

    def train(self, model: FLModel) -> Union[str, FLModel]:
        self._create_datasets()

        # get round information
        self.info(f"Current/Total Round: {self.current_round + 1}/{self.total_rounds}")
        self.info(f"Client identity: {self.site_name}")

        # update local model weights with received weights
        global_weights = model.params

        # Before loading weights, tensors might need to be reshaped to support HE for secure aggregation.
        local_var_dict = self.model.state_dict()
        model_keys = global_weights.keys()
        for var_name in local_var_dict:
            if var_name in model_keys:
                weights = global_weights[var_name]
                try:
                    # reshape global weights to compute difference later on
                    global_weights[var_name] = np.reshape(
                        weights, local_var_dict[var_name].shape
                    )
                    # update the local dict
                    local_var_dict[var_name] = torch.as_tensor(global_weights[var_name])
                except BaseException as e:
                    raise ValueError(f"Convert weight from {var_name} failed") from e
        self.model.load_state_dict(local_var_dict)

        # local steps
        epoch_len = len(self.train_loader)
        self.info(f"Local steps per epoch: {epoch_len}")

        # make a copy of model_global as reference for potential FedProx loss or SCAFFOLD
        model_global = copy.deepcopy(self.model)
        for param in model_global.parameters():
            param.requires_grad = False

        # local train
        self.local_train(train_loader=self.train_loader, model_global=model_global)
        self.epoch_of_start_time += self.aggregation_epochs

        # perform valid after local train
        acc = self.local_valid(self.valid_loader, tb_id="val_acc_local_model")
        self.info(f"val_acc_local_model: {acc:.4f}")

        # save model
        self.save_model(is_best=False)
        if acc > self.best_acc:
            self.best_acc = acc
            self.save_model(is_best=True)

        # compute delta model, global model has the primary key set
        local_weights = self.model.state_dict()
        model_diff = {}
        for name in global_weights:
            if name not in local_weights:
                continue
            model_diff[name] = np.subtract(
                local_weights[name].cpu().numpy(),
                global_weights[name],
                dtype=np.float32,
            )
            if np.any(np.isnan(model_diff[name])):
                self.stop_task(f"{name} weights became NaN...")
                return ReturnCode.EXECUTION_EXCEPTION

        # return an FLModel containing the model differences
        fl_model = FLModel(params_type=ParamsType.DIFF, params=model_diff)

        FLModelUtils.set_meta_prop(
            fl_model, FLMetaKey.NUM_STEPS_CURRENT_ROUND, epoch_len
        )
        self.info("Local epochs finished. Returning FLModel")
        return fl_model

    def get_model(self, model_name: str) -> Union[str, FLModel]:
        # Retrieve the best local model saved during training.
        if model_name == ModelName.BEST_MODEL:
            try:
                # load model to cpu as server might or might not have a GPU
                model_data = torch.load(self.best_local_model_file, map_location="cpu")
            except Exception as e:
                raise ValueError("Unable to load best model") from e

            # Create FLModel from model data.
            if model_data:
                # convert weights to numpy to support FOBS
                model_weights = model_data["model_weights"]
                for k, v in model_weights.items():
                    model_weights[k] = v.numpy()
                return FLModel(params_type=ParamsType.FULL, params=model_weights)
            else:
                # Set return code.
                self.error(
                    f"best local model not found at {self.best_local_model_file}."
                )
                return ReturnCode.EXECUTION_RESULT_ERROR
        else:
            raise ValueError(
                f"Unknown model_type: {model_name}"
            )  # Raised errors are caught in LearnerExecutor class.

    def local_valid(self, valid_loader, tb_id=None):
        self.model.eval()
        all_labels, all_probs, all_preds = [], [], []
        with torch.no_grad():
            for _i, (inputs, labels) in enumerate(valid_loader):
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                outputs = self.model(inputs)
                probs = torch.sigmoid(outputs)
                preds = (probs > 0.5).int()

                all_labels.append(labels.cpu().numpy())
                all_probs.append(probs.cpu().numpy())
                all_preds.append(preds.cpu().numpy())

            if all_labels:
                y_true = np.vstack(all_labels)
                y_prob = np.vstack(all_probs)
                y_pred = np.vstack(all_preds)

                # Accuracy (all classes must match exactly)
                acc = (y_pred == y_true).all(axis=1).mean() * 100.0

                # AUC (macro average across classes)
                try:
                    auc = roc_auc_score(
                        y_true, y_prob, average="macro", multi_class="ovr"
                    )
                except ValueError:
                    auc = float("nan")  # if only one class is present
            else:
                acc, auc = 0.0, float("nan")
            metric = acc
            if tb_id:
                self.writer.add_scalar(tb_id, metric, self.epoch_global)
        return metric

    def validate(self, model: FLModel) -> Union[str, FLModel]:
        self._create_datasets()

        # get validation information
        self.info(f"Client identity: {self.site_name}")

        # update local model weights with received weights
        global_weights = model.params

        # Before loading weights, tensors might need to be reshaped to support HE for secure aggregation.
        local_var_dict = self.model.state_dict()
        model_keys = global_weights.keys()
        n_loaded = 0
        for var_name in local_var_dict:
            if var_name in model_keys:
                weights = torch.as_tensor(global_weights[var_name], device=self.device)
                try:
                    # update the local dict
                    local_var_dict[var_name] = torch.as_tensor(
                        torch.reshape(weights, local_var_dict[var_name].shape)
                    )
                    n_loaded += 1
                except BaseException as e:
                    raise ValueError(f"Convert weight from {var_name} failed") from e
        self.model.load_state_dict(local_var_dict)
        if n_loaded == 0:
            raise ValueError(
                f"No weights loaded for validation! Received weight dict is {global_weights}"
            )

        # get validation meta info
        validate_type = FLModelUtils.get_meta_prop(
            model, FLMetaKey.VALIDATE_TYPE, ValidateType.MODEL_VALIDATE
        )  # TODO: enable model.get_meta_prop(...)
        model_owner = self.get_shareable_header(AppConstants.MODEL_OWNER)

        # perform valid
        train_acc = self.local_valid(
            self.train_loader,
            tb_id=(
                "train_acc_global_model"
                if validate_type == ValidateType.BEFORE_TRAIN_VALIDATE
                else None
            ),
        )
        self.info(f"training acc ({model_owner}): {train_acc:.4f}")

        val_acc = self.local_valid(
            self.valid_loader,
            tb_id=(
                "val_acc_global_model"
                if validate_type == ValidateType.BEFORE_TRAIN_VALIDATE
                else None
            ),
        )
        self.info(f"validation acc ({model_owner}): {val_acc:.4f}")
        self.info("Evaluation finished. Returning result")

        if val_acc > self.best_acc:
            self.best_acc = val_acc
            self.save_model(is_best=True)

        val_results = {"train_accuracy": train_acc, "val_accuracy": val_acc}
        return FLModel(metrics=val_results)

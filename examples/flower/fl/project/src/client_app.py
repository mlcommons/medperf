"""pytorchexample: A Flower / PyTorch app."""

import torch
from flwr.app import ArrayRecord, Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp

from task import test as test_fn
from task import train as train_fn
from models import SimpleCNN as Net
from data_loader import ChestXrayDataset

# Flower ClientApp
app = ClientApp()


@app.train()
def train(msg: Message, context: Context):
    """Train the model on local data."""
    # Load the model and initialize it with the received weights
    model = Net()
    model.load_state_dict(msg.content["arrays"].to_torch_state_dict())
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    train_dir = context.node_config["train_data_path"]
    train_labels_dir = context.node_config["train_labels_path"]

    # Load the data
    batch_size = context.run_config["batch-size"]
    trainloader = torch.utils.data.DataLoader(
        ChestXrayDataset(train_dir, train_labels_dir),
        batch_size=batch_size,
        shuffle=True,
    )

    # Call the training function
    train_loss = train_fn(
        model,
        trainloader,
        context.run_config["local-epochs"],
        msg.content["config"]["lr"],
        device,
    )

    # Construct and return reply Message
    model_record = ArrayRecord(model.state_dict())
    metrics = {
        "train_loss": train_loss,
        "num-examples": len(trainloader.dataset),
    }
    metric_record = MetricRecord(metrics)
    content = RecordDict({"arrays": model_record, "metrics": metric_record})
    return Message(content=content, reply_to=msg)


@app.evaluate()
def evaluate(msg: Message, context: Context):
    """Evaluate the model on local data."""
    val_dir = context.node_config["val_data_path"]
    val_labels_dir = context.node_config["val_labels_path"]

    # Load the model and initialize it with the received weights
    model = Net()
    model.load_state_dict(msg.content["arrays"].to_torch_state_dict())
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Load the data

    batch_size = context.run_config["batch-size"]
    valloader = torch.utils.data.DataLoader(
        ChestXrayDataset(val_dir, val_labels_dir),
        batch_size=batch_size,
        shuffle=False,
    )

    # Call the evaluation function
    eval_loss, eval_acc, eval_auc = test_fn(model, valloader, device)

    # Construct and return reply Message
    metrics = {
        "eval_loss": eval_loss,
        "eval_acc": eval_acc,
        "eval_auc": eval_auc,
        "num-examples": len(valloader.dataset),
    }
    metric_record = MetricRecord(metrics)
    content = RecordDict({"metrics": metric_record})
    return Message(content=content, reply_to=msg)

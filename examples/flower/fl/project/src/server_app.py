"""pytorchexample: A Flower / PyTorch app."""

import torch
import os
from flwr.app import ArrayRecord, ConfigRecord, Context
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

# Create ServerApp
app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    """Main entry point for the ServerApp."""
    init_weights_folder = os.environ["INITIAL_MODEL_PATH"]
    out_weights_folder = os.environ["OUTPUT_MODEL_PATH"]

    init_weights = os.path.join(init_weights_folder, "initial_model.pt")
    out_weights_path = os.path.join(out_weights_folder, "trained_model.pt")

    # Read run config
    num_rounds: int = context.run_config["num-server-rounds"]
    lr: float = context.run_config["learning-rate"]

    # Load global model weights
    arrays = ArrayRecord(torch.load(init_weights))

    # Initialize FedAvg strategy
    strategy = FedAvg()

    # Start strategy, run FedAvg for `num_rounds`
    result = strategy.start(
        grid=grid,
        initial_arrays=arrays,
        train_config=ConfigRecord({"lr": lr}),
        num_rounds=num_rounds,
    )

    # Save final model to disk
    print("\nSaving final model to disk...")
    state_dict = result.arrays.to_torch_state_dict()
    torch.save(state_dict, out_weights_path)

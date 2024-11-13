import os
import yaml

import pandas as pd
import typer

app = typer.Typer()

def create_metrics_dataframe(per_round_status):
    # concatenate all the 'metrics' lists
    lists = [r['metrics'] for r in per_round_status]
    metrics = [i for l in lists for i in l]
    return pd.DataFrame(metrics)

def load_status_yaml(training_id, server):
    with open(os.path.join(os.path.expanduser('~'), '.medperf/training', server, f"{training_id}", 'status.yaml'), 'r') as f:
        return yaml.safe_load(f)

@app.command()
def parse(    
    training_id: int = typer.Option(1, "-t", "--training_id"),
    server:      str = typer.Option('api_medperf_org', '-s', '--server')
):
    status_yaml = load_status_yaml(training_id, server)
    
    df = create_metrics_dataframe(status_yaml)
    df.to_csv('metrics.csv')


if __name__ == "__main__":
    app()

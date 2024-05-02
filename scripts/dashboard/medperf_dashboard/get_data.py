import os
import pandas as pd
import datetime

from medperf.entities.dataset import Dataset
from medperf import config

from .utils import get_institution_from_email, get_reports_path, stage_id2name

from typer import Typer, Option, run

app = Typer()


def get_dsets(mlcube_id):
    dsets = Dataset.all(filters={"mlcube": mlcube_id})
    dsets = [dset.todict() for dset in dsets]
    for dset in dsets:
        user_id = dset["owner"]
        dset["user"] = config.comms.get_user(user_id)

    return dsets


def build_dset_df(dsets, user2institution, stages_df):
    formatted_dsets = []
    for dset in dsets:
        email = dset["user"]["email"]
        institution = get_institution_from_email(email, user2institution)
        formatted_dset = {
            "name": dset["name"],
            "owner": dset["owner"],
            "email": email,
            "is_valid": dset["is_valid"],
            "created_at": dset["created_at"],
            "modified_at": dset["modified_at"],
            "institution": institution,
        }
        if len(dset["report"]):
            # Contains a readable report
            report = dset["report"]
            exec_status = report["execution_status"]
            formatted_dset["execution_status"] = exec_status
            formatted_dset["progress"] = report["progress"]

        formatted_dsets.append(formatted_dset)
        dsets_df = pd.DataFrame(formatted_dsets)

        progress = dsets_df["progress"].fillna({})
        progress_df = pd.DataFrame(progress.values.tolist())
        progress_df.rename(columns=lambda x: stage_id2name(x, stages_df), inplace=True)
        progress_df = progress_df.fillna("0.0%").map(lambda x: float(x[:-1]) / 100)
        progress_df = progress_df.groupby(level=0, axis=1).sum()

        full_table = dsets_df.join(progress_df)
        full_table = full_table[full_table["is_valid"]]
        full_table.drop(columns=["owner", "progress"], inplace=True)

    return full_table


def write_dsets_df(dsets_df, full_path):
    timenow = datetime.datetime.now(datetime.timezone.utc)

    full_table = dsets_df
    latest_table = full_table.sort_values("modified_at").groupby("institution").last()
    latest_table = latest_table.loc[:, (latest_table != 0).any(axis=0)]

    full_table_path = os.path.join(full_path, "full_table.csv")
    latest_table_path = os.path.join(full_path, "latest_table.csv")
    timestamp_path = os.path.join(full_path, f"{timenow}.csv")

    full_table.to_csv(full_table_path)
    full_table.to_csv(timestamp_path)
    latest_table.to_csv(latest_table_path)


def write_sites(dsets_df, institutions_df, full_path):
    sites_path = os.path.join(full_path, "sites.txt")

    expected_sites = institutions_df["institution"].values.tolist()
    registered_sites = dsets_df["institution"].values.tolist()
    sites = list(set(expected_sites + registered_sites))

    with open(sites_path, "w") as f:
        f.write("\n".join(sites))


def get_data(mlcube_id, stages_path, institutions_path, out_path):
    dsets = get_dsets(mlcube_id)
    full_path = get_reports_path(out_path, mlcube_id)
    os.makedirs(full_path, exist_ok=True)

    institutions_df = pd.read_csv(institutions_path)
    user2institution = {u: i for i, u in institutions_df.values.tolist()}
    stages_df = pd.read_csv(stages_path)
    stages_df.set_index("Status Code", inplace=True)

    dsets_df = build_dset_df(dsets, user2institution, stages_df)
    write_dsets_df(dsets_df, full_path)
    write_sites(dsets_df, institutions_df, full_path)


@app.command()
def main(
    mlcube_id: int = Option(
        ..., "-m", "--mlcube", help="MLCube ID to inspect prparation from"
    ),
    stages_path: str = Option(
        "assets/stages.csv", "-s", "--stages", help="Path to stages.csv"
    ),
    institutions_path: str = Option(
        ...,
        "-i",
        "--institutions",
        help="Path to a CSV file containing institution-email information",
    ),
    out_path: str = Option(
        "reports", "-o", "--out-path", help="location to store progress CSVs"
    ),
):
    get_data(mlcube_id, stages_path, institutions_path, out_path)


if __name__ == "__main__":
    run(main)

import os
from dash import Dash, html, dcc, dash_table
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd

from get_data import get_data
from utils import get_reports_path

from typer import Typer, run, Option

t_app = Typer()


def participant_dashboard(latest_table: pd.DataFrame, sites: pd.DataFrame):
    values = sites["registered"].value_counts().sort_values().values.tolist()
    fig = go.Figure(
        [go.Pie(labels=["Registered", "Not registered"], values=values, hole=0.5)]
    )
    fig.update_traces(textinfo="value")
    fig.add_annotation(
        text=f"{sum(values)}",
        x=0.5,
        y=0.5,
        font=dict(size=20),
        showarrow=False,
    )
    fig.update_layout(
        autosize=False,
        width=500,
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=True,
    )
    truncated_sites = sites.copy()
    truncated_sites["site"] = truncated_sites["site"].apply(
        lambda x: x[:40] + "..." if len(x) > 32 else x
    )
    table_data = truncated_sites.sort_values(by="registered", ascending=False)

    return dbc.Container(
        [
            html.H2("Hospital Participation", style={"TextAlign": "center"}),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dash_table.DataTable(
                                data=table_data.to_dict("records"),
                                page_size=14,
                            ),
                        ],
                        className="align-middle col-6",
                    ),
                    dbc.Col(
                        [
                            dcc.Graph(figure=fig, responsive=True),
                        ],
                        className="col-6",
                    ),
                ]
            ),
        ],
        className="bg-secondary p-4 card mt-4",
    )


def preparation_status_dashboard(latest_table: pd.DataFrame, stages_colors, stages_df):
    all_stages_list = stages_df["status_name"].values.tolist()
    all_stages = set(all_stages_list)
    table_cols = set(latest_table.columns)
    reported_stages = all_stages.intersection(table_cols)
    sorted_reported_stages = [
        stage for stage in all_stages_list if stage in reported_stages
    ]

    stages = latest_table[sorted_reported_stages]
    stages["Unknown"] = 1 * (stages.sum(axis=1) == 0)
    stages_amount = stages.sum().sort_values(ascending=False)
    stages_amount = stages_amount[stages_amount > 0]
    stages_total = stages_amount.sum()

    stages_fig = px.pie(
        stages_amount,
        names=stages_amount.index,
        values=stages_amount.values,
        hole=0.5,
        color=stages_amount.index,
        color_discrete_map=stages_colors,
        title="Overall stages distribution",
    )
    stages_fig.add_annotation(
        text=f"{int(stages_total.round())}",
        x=0.5,
        y=0.5,
        font=dict(size=20),
        showarrow=False,
    )
    stages_fig.update_layout(
        autosize=False,
        width=500,
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=True,
    )

    exec_status = latest_table[["email", "execution_status"]]
    num_exec_status = exec_status.fillna("NA").groupby("execution_status").count()
    exec_status_dist = num_exec_status / num_exec_status.sum()
    exec_status_dist.rename(columns={"email": "distribution"}, inplace=True)

    exec_fig = px.pie(
        exec_status_dist,
        names=exec_status_dist.index,
        values=exec_status_dist.values.flatten(),
        title="Execution status distribution",
        color=exec_status_dist.index,
        color_discrete_map={
            "finished": "mediumseagreen",
            "NA": "mediumturquoise",
            "running": "cornflowerblue",
            "failed": "orangered",
        },
    )

    char_limit = 12

    institution_stages = stages.loc[:, (stages != 0).any(axis=0)].join(
        latest_table["email"]
    )
    institution_stages["email"] = institution_stages["email"].apply(
        lambda x: x[:char_limit] + "..." if len(x) > char_limit else x
    )
    institution_stages = institution_stages.sort_values(
        by=sorted_reported_stages, ascending=False
    )
    institution_stages = institution_stages.set_index("email")
    stages_per_person_fig = px.bar(
        institution_stages * 100,  # Convert to percentages
        institution_stages.index,
        y=institution_stages.columns.to_list(),
        color_discrete_map=stages_colors,
        title="Stages distribution per user",
    )
    stages_per_person_fig.update_xaxes(tickangle=45)
    stages_per_person_fig.update_layout(yaxis_ticksuffix="%", yaxis_title="Percentage")

    return dbc.Container(
        [
            html.H2("Preparation Status", style={"TextAlign": "center"}),
            dbc.Row(
                [
                    dbc.Col(
                        [dcc.Graph(figure=stages_fig, responsive=True)],
                        className="col-6",
                    ),
                    dbc.Col(
                        [dcc.Graph(figure=exec_fig, responsive=True)], className="col-6"
                    ),
                ],
                className="collapse show",
                id="prep-status-all",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [dcc.Graph(figure=stages_per_person_fig, responsive=True)],
                        id="prep-status-user",
                    ),
                ],
                className="mt-4",
            ),
        ],
        className="card bg-secondary p-4 mt-4 mb-4",
    )


def preparation_timeline(stages_colors, stages_df, full_path):
    all_stages_list = stages_df["status_name"].values.tolist()
    all_stages = set(all_stages_list)

    reports = os.listdir(full_path)
    timeseries_reports = list(
        set(reports) - set(["full_table.csv", "latest_table.csv", "sites.txt"])
    )
    timeseries_df = None
    for report_file in timeseries_reports:
        reportpath = os.path.join(full_path, report_file)
        report_df = pd.read_csv(reportpath)

        report_df["datetime"] = pd.to_datetime(report_file[:-10])
        report_df = report_df.sort_values("modified_at").groupby("institution").last()
        if timeseries_df is None:
            timeseries_df = report_df
        else:
            timeseries_df = pd.concat([timeseries_df, report_df])

    table_cols = set(report_df.columns)
    reported_stages = all_stages.intersection(table_cols)
    sorted_reported_stages = [
        stage for stage in all_stages_list if stage in reported_stages
    ]
    cols_indices = sorted_reported_stages + ["datetime"]

    timeseries_stages = timeseries_df[cols_indices].set_index("datetime")
    timeseries_stages.sum(axis=1)
    timeseries_stages = timeseries_df[cols_indices].set_index("datetime")
    timeseries_stages["Unknown"] = 1 * (timeseries_stages.sum(axis=1) == 0)
    timeseries_totals = timeseries_stages.groupby(timeseries_stages.index).sum()
    timeseries_totals = timeseries_totals.loc[:, (timeseries_totals != 0).any(axis=0)]
    fig = px.area(
        timeseries_totals,
        x=timeseries_totals.index,
        y=timeseries_totals.columns,
        color_discrete_map=stages_colors,
        title="Overall preparation progress over time",
    )

    return dbc.Container(
        [
            html.H2("RANO Timeline", style={"TextAlign": "center"}),
            dbc.Row(
                [
                    dbc.Col([dcc.Graph(figure=fig, responsive=True)]),
                ],
                className="mt-4",
            ),
        ],
        className="card bg-secondary p-4 mt-4",
    )


def get_sites_dicts(sites_path, latest_table):
    with open(sites_path, "r") as f:
        sites = f.readlines()
    sites = [site.strip() for site in sites]
    sites += latest_table["institution"].values.tolist()
    sites_dicts = [
        {"site": site, "registered": site in set(latest_table["institution"])}
        for site in sites
    ]
    return sites_dicts


def build_dash_app(registered_df, stages_colors, latest_table, stages, full_path):
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.LUMEN],
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=1.0",
            }
        ],
    )

    app.layout = dbc.Container(
        [
            html.H1(children="RANO Progress", style={"textAlign": "center"}),
            participant_dashboard(latest_table, registered_df),
            preparation_status_dashboard(latest_table, stages_colors, stages),
            preparation_timeline(stages_colors, stages, full_path),
        ]
    )

    return app


@t_app.command()
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
    full_path = get_reports_path(out_path, mlcube_id)

    latest_path = os.path.join(full_path, "latest_table.csv")
    latest_table = pd.read_csv(latest_path)

    sites_path = os.path.join(full_path, "sites.txt")
    sites_dicts = get_sites_dicts(sites_path, latest_table)

    registered_df = pd.DataFrame(sites_dicts)
    registered_df = registered_df.drop_duplicates()

    stages = pd.read_csv(stages_path)
    stages_colors = (
        stages[["status_name", "color"]].set_index("status_name").to_dict()["color"]
    )
    stages_colors["Unknown"] = "silver"

    app = build_dash_app(registered_df, stages_colors, latest_table, stages, full_path)
    app.run_server(debug=True)


if __name__ == "__main__":
    run(main)

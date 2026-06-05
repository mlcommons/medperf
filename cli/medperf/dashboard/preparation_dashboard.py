import os
from dash import Dash, html, dcc, dash_table
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd

from medperf import config
from medperf.utils import sanitize_path

from .get_data import get_data
from .utils import get_reports_path

from typer import Typer, run, Option

t_app = Typer()

_DASH_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_MEDPERF_FONT = "'Inter', ui-sans-serif, system-ui, sans-serif"

# Match base.html: html.dark + localStorage medperf-dark (iframe does not inherit parent DOM).
_MEDPERF_DASH_INDEX_STRING = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        <script>
        (function(){
          try {
            var v = localStorage.getItem('medperf-dark');
            var match = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            var dark = v === '1' || (v === null && match);
            if (dark) document.documentElement.classList.add('dark');
            else document.documentElement.classList.remove('dark');
          } catch (e) {}
        })();
        </script>
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

_EXEC_STATUS_COLORS = {
    "finished": "#2e7d32",
    "NA": "#78909c",
    "running": "#1565c0",
    "failed": "#c62828",
}

_PARTICIPATION_COLORS = ["#2e7d32", "#90a4ae"]


def _apply_medperf_chart_theme(fig):
    """Typography and axes styling aligned with MedPerf WebUI."""
    fig.update_layout(
        font=dict(family=_MEDPERF_FONT, size=13, color="#374151"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f9fafb",
        title=dict(font=dict(size=16, color="#1f2937", family=_MEDPERF_FONT)),
        legend=dict(
            font=dict(family=_MEDPERF_FONT, size=12),
            bgcolor="rgba(249,250,251,0.95)",
            bordercolor="#e5e7eb",
            borderwidth=1,
        ),
        autosize=True,
        margin=dict(l=48, r=28, t=64, b=48),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#e5e7eb",
        zerolinecolor="#d1d5db",
        linecolor="#9ca3af",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#e5e7eb",
        zerolinecolor="#d1d5db",
        linecolor="#9ca3af",
    )
    return fig


def _datatable():
    return {
        "style_table": {"overflowX": "auto"},
        "style_cell": {
            "fontFamily": _MEDPERF_FONT,
            "fontSize": "14px",
            "padding": "10px 12px",
            "border": "1px solid #e5e7eb",
            "textAlign": "left",
        },
        "style_header": {
            "backgroundColor": "#e8f5e9",
            "color": "#1b5e20",
            "fontWeight": "700",
            "border": "none",
            "fontFamily": _MEDPERF_FONT,
        },
        "style_data": {"border": "none"},
        "css": [
            {
                "selector": ".dash-spreadsheet-container",
                "rule": "border-radius: 12px; font-family: " + _MEDPERF_FONT + ";",
            },
        ],
    }


def participant_dashboard(latest_table: pd.DataFrame, sites: pd.DataFrame):
    values = sites["registered"].value_counts().sort_values().values.tolist()
    fig = go.Figure(
        [go.Pie(labels=["Registered", "Not registered"], values=values, hole=0.5)]
    )
    fig.update_traces(
        textinfo="value",
        marker=dict(colors=_PARTICIPATION_COLORS, line=dict(color="#fff", width=2)),
    )
    fig.add_annotation(
        text=f"{sum(values)}",
        x=0.5,
        y=0.5,
        font=dict(size=20, family=_MEDPERF_FONT, color="#1f2937"),
        showarrow=False,
    )
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=56, b=20),
        showlegend=True,
    )
    _apply_medperf_chart_theme(fig)

    truncated_sites = sites.copy()
    truncated_sites["site"] = truncated_sites["site"].apply(
        lambda x: x[:40] + "..." if len(x) > 32 else x
    )
    table_data = truncated_sites.sort_values(by="registered", ascending=False)
    dt = _datatable()

    return html.Div(
        [
            html.H2("Participation"),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                dash_table.DataTable(
                                    data=table_data.to_dict("records"),
                                    page_size=14,
                                    **dt,
                                ),
                            ],
                            className="medperf-dash-table-wrap",
                        ),
                        md=6,
                        className="mb-4 mb-md-0",
                    ),
                    dbc.Col(
                        [
                            dcc.Graph(
                                figure=fig,
                                responsive=True,
                                config={"displayModeBar": True},
                            )
                        ],
                        md=6,
                    ),
                ],
                className="g-3",
            ),
        ],
        className="medperf-dash-section",
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
        font=dict(size=20, family=_MEDPERF_FONT, color="#1f2937"),
        showarrow=False,
    )
    stages_fig.update_layout(
        height=400, margin=dict(l=20, r=20, t=56, b=20), showlegend=True
    )
    stages_fig.update_traces(marker=dict(line=dict(color="#fff", width=2)))
    _apply_medperf_chart_theme(stages_fig)

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
        color_discrete_map=_EXEC_STATUS_COLORS,
    )
    exec_fig.update_layout(
        height=400, margin=dict(l=20, r=20, t=56, b=20), showlegend=True
    )
    exec_fig.update_traces(marker=dict(line=dict(color="#fff", width=2)))
    _apply_medperf_chart_theme(exec_fig)

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
        institution_stages * 100,
        institution_stages.index,
        y=institution_stages.columns.to_list(),
        color_discrete_map=stages_colors,
        title="Stages distribution per user",
    )
    stages_per_person_fig.update_xaxes(tickangle=45)
    stages_per_person_fig.update_layout(
        yaxis_ticksuffix="%",
        yaxis_title="Percentage",
        height=480,
        margin=dict(l=48, r=28, t=64, b=120),
    )
    _apply_medperf_chart_theme(stages_per_person_fig)

    return html.Div(
        [
            html.H2("Preparation Status"),
            dbc.Row(
                [
                    dbc.Col(
                        [dcc.Graph(figure=stages_fig, responsive=True)],
                        md=6,
                        className="mb-4 mb-md-0",
                    ),
                    dbc.Col(
                        [dcc.Graph(figure=exec_fig, responsive=True)],
                        md=6,
                    ),
                ],
                className="g-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [dcc.Graph(figure=stages_per_person_fig, responsive=True)],
                        width=12,
                        className="mt-3",
                    ),
                ],
            ),
        ],
        className="medperf-dash-section",
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
    fig.update_layout(height=420, margin=dict(l=48, r=28, t=64, b=48))
    _apply_medperf_chart_theme(fig)

    return html.Div(
        [
            html.H2("Preparation Timeline"),
            dbc.Row(
                [
                    dbc.Col([dcc.Graph(figure=fig, responsive=True)]),
                ],
                className="mt-2",
            ),
        ],
        className="medperf-dash-section",
    )


def no_data_layout():
    return dbc.Container(
        [
            html.H1(
                "Preparation Progress",
                className="medperf-dash-title text-center",
            ),
            dbc.Alert(
                [
                    html.H4("No registered datasets", className="alert-heading mb-3"),
                    html.P(
                        "There are no datasets registered with the data preparator "
                        "of this benchmark yet.",
                        className="mb-0 lead",
                    ),
                ],
                color="warning",
                className="mt-4 text-center medperf-dash-alert shadow-sm",
            ),
        ],
        fluid=True,
        className="medperf-dash-main py-3",
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


def _build_dash_app(
    data_exists,
    registered_df,
    stages_colors,
    latest_table,
    stages,
    full_path,
    prefix,
):

    app = Dash(
        __name__,
        title="Preparation Dashboard",
        requests_pathname_prefix=prefix,
        assets_folder=_DASH_ASSETS,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=1.0",
            }
        ],
    )
    app.index_string = _MEDPERF_DASH_INDEX_STRING

    if not data_exists:
        app.layout = no_data_layout()
        return app

    app.layout = dbc.Container(
        [
            html.H1(
                children="Preparation Progress",
                className="medperf-dash-title text-center",
            ),
            participant_dashboard(latest_table, registered_df),
            preparation_status_dashboard(latest_table, stages_colors, stages),
            preparation_timeline(stages_colors, stages, full_path),
        ],
        fluid=True,
        className="medperf-dash-main py-2",
    )

    return app


def build_app(
    benchmark_id,
    stages_path,
    institutions_path,
    out_path=None,
    prefix=None,
):
    out_path = sanitize_path(out_path) or config.dashboards_folder
    full_path = get_reports_path(out_path, benchmark_id)

    data_exists = get_data(benchmark_id, stages_path, institutions_path, full_path)

    registered_df = None
    stages_colors = None
    latest_table = None
    stages = None

    if data_exists:
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
        stages_colors["Unknown"] = "#9e9e9e"

    return _build_dash_app(
        data_exists,
        registered_df,
        stages_colors,
        latest_table,
        stages,
        full_path,
        prefix,
    )


@t_app.command()
def main(
    benchmark_id: int = Option(
        ..., "-b", "--benchmark", help="Benchmark ID to inspect preparation from"
    ),
    stages_path: str = Option(..., "-s", "--stages", help="Path to stages.csv"),
    institutions_path: str = Option(
        ...,
        "-i",
        "--institutions",
        help="Path to a CSV file containing institution-email information",
    ),
    out_path: str = Option(
        None, "-o", "--out-path", help="location to store progress CSVs"
    ),
):
    app = build_app(benchmark_id, stages_path, institutions_path, out_path)
    app.run_server(debug=True)


if __name__ == "__main__":
    run(main)

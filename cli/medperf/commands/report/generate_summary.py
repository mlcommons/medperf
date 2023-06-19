import os
import yaml
import pandas as pd
from time import strftime, localtime

from medperf import config
from medperf.utils import storage_path


class SummaryGenerator:
    @staticmethod
    def run(
        in_data_hash: str,
        prep_cube_uid: int,
        out_summary_path: str,
        benchmark_uid: int = None,
    ):
        template_path = "../../assets/summary_template.md"
        template_task_path = "../../assets/summary_task_template.md"
        dirname = os.path.dirname(__file__)
        template_path = os.path.join(dirname, template_path)
        template_task_path = os.path.join(dirname, template_task_path)

        staging_path = storage_path(config.staging_data_storage)
        out_path = os.path.join(staging_path, f"{in_data_hash}_{prep_cube_uid}")
        report_path = os.path.join(out_path, config.report_file)
        data_path = os.path.join(out_path, "data")
        labels_path = os.path.join(out_path, "labels")

        with open(template_path, "r") as f:
            template = f.read()
        with open(template_task_path, "r") as f:
            task_template = f.read()

        modified_at = os.path.getmtime(report_path)
        modified_at_str = strftime("%Y-%m-%d %H:%M:%S", localtime(modified_at))
        with open(report_path, "r") as f:
            report = yaml.safe_load(f)

        report_df = pd.DataFrame(report)
        percents_df = 100 * report_df["status_name"].value_counts() / len(report_df)
        if "DONE" not in percents_df:
            percents_df["DONE"] = 0

        # Sort so that DONE is first, and then is in descending order
        percents_df.sort_values(ascending=False, inplace=True)
        idxs = ["DONE"] + [idx for idx in percents_df.index if idx != "DONE"]
        percents_df = percents_df[idxs].round().astype(int)

        # TODO: create body
        body = ""
        for status, pct in percents_df.items():
            name = status.replace("_", " ").capitalize()
            title = f"#### ![](https://geps.dev/progress/{pct}) {name}"
            cases = report_df[report_df["status_name"] == status]
            cases["data_path"] = cases["data_path"].apply(
                lambda x: os.path.join(data_path, x)
            )
            cases["labels_path"] = cases["labels_path"].apply(
                lambda x: os.path.join(labels_path, x)
            )
            desc = ""
            tasks = []
            if len(cases):
                desc = cases["comment"].iloc[0]
                if desc:
                    # If no comment is available, then the user doesn't need to
                    # do anything here.
                    # Don't show unnecessary information for such cases
                    tasks = cases.apply(
                        lambda x: task_template.format(
                            id=x.name, data_path=x.data_path, label_path=x.labels_path
                        ),
                        axis=1,
                    )
                    tasks = tasks.to_list()

            status_body = "\n".join([title] + [desc] + tasks)
            body = "\n".join([body, status_body])

        summary = template.format(
            input_hash=in_data_hash,
            prep_cube=prep_cube_uid,
            benchmark=benchmark_uid,
            last_edited=modified_at_str,
            body=body,
        )
        with open(out_summary_path, "w") as f:
            f.write(summary)

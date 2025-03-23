import os

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.kbs import KBS
from medperf.utils import generate_tmp_uid, create_init_data, generate_tmp_path
import medperf.config as config
import base64
import subprocess


class TrustedExecution:
    @classmethod
    def run(cls, dataset: Dataset, model: Cube, evaluator: Cube):

        dataset_kbs: KBS = KBS.get(dataset.user_metadata["kbs"])
        model_kbs: KBS = KBS.get(model.user_metadata["kbs"])
        attest_service: KBS = KBS.get(model_kbs.config["as"])

        with open(config.pod_template_path) as f:
            contents = f.read()

        initdata = create_init_data(
            attest_service.config["address"],
            attest_service.config["port"],
            attest_service.config["kbs_port"],
            model_kbs.config["address"],
            model_kbs.config["port"],
            attest_service.config["cert"],
            model_kbs.config["cert"],
        )

        random_uid = generate_tmp_uid()[:8]

        pod_name = f"{dataset.id}_{model.id}_{evaluator.id}_{random_uid}"
        model_container_name = f"model_{random_uid}"
        metrics_container_name = f"metrics_{random_uid}"

        contents = contents.format(
            pod_name=pod_name,
            initdata=initdata,
            model_container_name=model_container_name,
            model_container_image=model.get_image(),
            kbs_cert=base64.b64encode(dataset_kbs.config["cert"].encode()).decode(),
            kbs_address=dataset_kbs.config["address"],
            kbs_port=dataset_kbs.config["port"],
            secret_id=dataset.secret_id,
            metrics_container_name=metrics_container_name,
            metrics_container_image=evaluator.get_image(),
        )

        workdir = generate_tmp_path()
        pod_path = os.path.join(workdir, "pod.yaml")
        with open(pod_path, "w") as f:
            f.write(contents)

        command = ["kubectl", "apply", "-k", "pod.yaml"]
        subprocess.run(command, cwd=workdir)

import os

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.entities.kbs import KBS
from medperf.utils import generate_tmp_uid, create_init_data, generate_tmp_path
import medperf.config as config
import base64
import subprocess


class TrustedExecution:
    @classmethod
    def run(cls, dataset: Dataset, model: Cube, evaluator: Cube, benchmark: Benchmark):

        dataset_kbs: KBS = KBS.get(dataset.user_metadata["kbs"])
        model_kbs: KBS = KBS.get(model.user_metadata["kbs"])
        attest_service: KBS = KBS.get(model_kbs.config["as"])

        with open(config.pod_template_path) as f:
            contents = f.read()

        model_container_image = model.get_encrypted_image()
        model_container_image = model_container_image + "@" + model.user_metadata["encrypted_digest"]

        metrics_container_image = evaluator.get_image()
        metrics_container_image = metrics_container_image + "@" + evaluator.user_metadata["digest"]

        initdata = create_init_data(
            attest_service.config["address"],
            attest_service.config["port"],
            attest_service.config["kbs_port"],
            model_kbs.config["address"],
            model_kbs.config["port"],
            attest_service.config["cert"],
            model_kbs.config["cert"],
            metrics_image=metrics_container_image,
            model_image=model_container_image
        )

        random_uid = generate_tmp_uid()[:8]

        pod_name = f"{dataset.id}-{model.id}-{evaluator.id}-{random_uid}"
        model_container_name = f"model-{random_uid}"
        metrics_container_name = f"metrics-{random_uid}"

        contents = contents.format(
            pod_name=pod_name,
            initdata=initdata,
            model_container_name=model_container_name,
            model_container_image=model_container_image,
            kbs_cert=base64.b64encode(dataset_kbs.config["cert"].encode()).decode(),
            kbs_address=dataset_kbs.config["address"],
            kbs_port=dataset_kbs.config["port"],
            secret_id=dataset.secret_id,
            metrics_container_name=metrics_container_name,
            metrics_container_image=metrics_container_image,
            benchmark_cert=base64.b64encode(benchmark.user_metadata["cert"].encode()).decode(),
            result_upload_url=benchmark.user_metadata["result_upload_url"],
        )

        workdir = generate_tmp_path()
        config.tmp_paths.remove(workdir)
        os.makedirs(workdir, exist_ok=True)
        pod_path = os.path.join(workdir, "pod.yaml")
        with open(pod_path, "w") as f:
            f.write(contents)
        config.ui.print(f"Path to pod: {workdir}")
        command = ["kubectl", "apply", "-f", "./pod.yaml"]
        subprocess.check_call(command, cwd=workdir)

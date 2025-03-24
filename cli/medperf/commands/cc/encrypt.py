import os
from medperf.utils import generate_tmp_uid, generate_tmp_path, remove_path
from medperf.entities.kbs import KBS
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.exceptions import MedperfException
import base64
import json


class ImageEncryption:
    @classmethod
    def run(cls, model_id, target):
        model = Cube.get(model_id)
        source_image = model.get_image()
        kbs_id = model.user_metadata["kbs"]
        kbs: KBS = KBS.get(kbs_id)
        key_id = f"default/image-kek/{generate_tmp_uid()}"
        script = os.path.join(os.path.dirname(__file__), "scripts/encrypt_image.sh")
        os.system(f"bash {script} -s {source_image} -t {target} -i {key_id} -k {kbs.kbs_storage}")
        model.update_metadata({"encrypted_image": target})


class DataEncryption:
    @classmethod
    def run(cls, dataset_id, output_folder, url):
        if not os.path.exists(output_folder) or not os.path.isabs(output_folder):
            raise MedperfException("Absolute path needed as an output folder")
        dataset = Dataset.get(dataset_id)
        kbs: KBS = KBS.get(dataset.user_metadata["kbs"])
        key_path = generate_tmp_path()
        output_encrypted_data = os.path.join(output_folder, "data.enc")
        script = os.path.join(os.path.dirname(__file__), "scripts/encrypt_data.sh")
        os.system(f"bash {script} -d {dataset.path} -e {output_encrypted_data} -s {key_path}")
        with open(key_path, "rb") as f:
            decryption_key = f.read()
        remove_path(key_path)
        secret = {"url": url, "decryption_key": base64.b64encode(decryption_key).decode()}
        secret_path = os.path.join(kbs.kbs_storage, dataset.secret_id)
        os.makedirs(os.path.dirname(secret_path), exist_ok=True)
        with open(secret_path, "w") as f:
            json.dump(secret, f)

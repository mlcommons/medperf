import os
from medperf import config
from medperf.entities.kbs import KBS
import shutil


class SubmitKbs:
    @classmethod
    def run(
        cls,
        address,
        port,
        attestation_service,
        key_path,
        crt_path,
        admin_private_key_path,
        admin_public_key_path,
    ):
        name = address.replace(".", "_") + str(port)
        with open(crt_path) as f:
            cert_txt = f.read()

        kbs_dict = config.comms.upload_kbs(
            {
                "name": name,
                "kbs_type": "kbs",
                "config": {
                    "address": address,
                    "port": port,
                    "cert": cert_txt,
                    "as": attestation_service,
                },
            }
        )
        kbs_obj = KBS(**kbs_dict)
        kbs_obj.write()

        os.makedirs(os.path.dirname(kbs_obj.key_path), exist_ok=True)
        os.makedirs(os.path.dirname(kbs_obj.cert_path), exist_ok=True)
        shutil.copyfile(key_path, kbs_obj.key_path)
        shutil.copyfile(crt_path, kbs_obj.cert_path)
        shutil.copyfile(admin_private_key_path, kbs_obj.admin_private_key_path)
        shutil.copyfile(admin_public_key_path, kbs_obj.admin_public_key_path)

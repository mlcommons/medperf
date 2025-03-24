import os
from medperf import config
from medperf.entities.kbs import KBS
import shutil


class SubmitAs:
    @classmethod
    def run(
        cls,
        address,
        port,
        kbs_port,
        rvps_port,
        key_path,
        crt_path,
        verification_key_path,
        verification_crt_path,
        admin_private_key_path,
        admin_public_key_path,
    ):
        name = address.replace(".", "_") + str(port)
        with open(crt_path) as f:
            cert_txt = f.read()

        with open(verification_crt_path) as f:
            verification_cert_txt = f.read()

        config.ui.print("Registering...")
        as_dict = config.comms.upload_kbs(
            {
                "name": name,
                "kbs_type": "as",
                "config": {
                    "address": address,
                    "port": port,
                    "kbs_port": kbs_port,
                    "rvps_port": rvps_port,
                    "cert": cert_txt,
                    "verification_cert": verification_cert_txt,
                },
            }
        )
        config.ui.print("Writing to disk...")
        as_obj = KBS(**as_dict)
        as_obj.write()
        os.makedirs(os.path.dirname(as_obj.key_path), exist_ok=True)
        os.makedirs(os.path.dirname(as_obj.cert_path), exist_ok=True)
        os.makedirs(os.path.dirname(as_obj.verification_key_path), exist_ok=True)
        os.makedirs(os.path.dirname(as_obj.verification_cert_path), exist_ok=True)
        shutil.copyfile(key_path, as_obj.key_path)
        shutil.copyfile(crt_path, as_obj.cert_path)
        shutil.copyfile(verification_key_path, as_obj.verification_key_path)
        shutil.copyfile(verification_crt_path, as_obj.verification_cert_path)
        shutil.copyfile(admin_private_key_path, as_obj.admin_private_key_path)
        shutil.copyfile(admin_public_key_path, as_obj.admin_public_key_path)

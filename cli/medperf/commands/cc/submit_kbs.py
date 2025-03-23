import os
from medperf import config
from medperf.utils import generate_tmp_path
from medperf.entities.kbs import KBS


class SubmitKbs:
    @classmethod
    def run(cls, address, port, attestation_service):
        key_path = generate_tmp_path()
        crt_path = generate_tmp_path()
        script = os.path.join(os.path.dirname(__file__), "scripts/generate_cert.sh")
        os.system(f"bash {script} -a {address} -c {crt_path} -k {key_path}")

        with open(crt_path) as f:
            cert_txt = f.read()

        kbs_dict = config.comms.upload_kbs(
            {
                "name": address,
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

        os.rename(key_path, kbs_obj.key_path)
        os.rename(crt_path, kbs_obj.cert_path)

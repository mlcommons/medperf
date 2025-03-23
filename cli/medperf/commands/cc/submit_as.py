import os
from medperf import config
from medperf.utils import generate_tmp_path
from medperf.entities.kbs import KBS


class SubmitAs:
    @classmethod
    def run(cls, address, port, kbs_port, rvps_port):
        name = address.replace(".", "_")
        key_path = generate_tmp_path()
        crt_path = generate_tmp_path()
        verification_key_path = generate_tmp_path()
        verification_crt_path = generate_tmp_path()

        script1 = os.path.join(os.path.dirname(__file__), "scripts/generate_cert.sh")
        os.system(f"bash {script1} -a {address} -c {crt_path} -k {key_path}")
        with open(crt_path) as f:
            cert_txt = f.read()

        script2 = os.path.join(os.path.dirname(__file__), "scripts/generate_verification_cert.sh")
        os.system(f"bash {script2} -n {name} -c {verification_crt_path} -k {verification_key_path}")
        with open(verification_crt_path) as f:
            verification_cert_txt = f.read()

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
        as_obj = KBS(**as_dict)
        as_obj.write()
        os.rename(key_path, as_obj.key_path)
        os.rename(crt_path, as_obj.cert_path)
        os.rename(verification_key_path, as_obj.verification_key_path)
        os.rename(verification_crt_path, as_obj.verification_cert_path)

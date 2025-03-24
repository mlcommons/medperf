from flask import Flask, request
import yaml
from pprint import pprint
import sys
import os

app = Flask(__name__)


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    file.save(f"{file.filename}")
    with open(f"{file.filename}") as f:
        results = yaml.safe_load(f)
    pprint(results)


if __name__ == "__main__":
    base_path = sys.argv[1]
    crt_path = os.path.join(base_path, "bmk.crt")
    key_path = os.path.join(base_path, "bmk.key")
    app.run(host="0.0.0.0", port=5507, ssl_context=(crt_path, key_path))

from setuptools import setup
from medperf._version import __version__

with open("requirements.txt", "r") as f:
    requires = []
    for line in f:
        if line.startswith("mlcube"):
            requires.append(line)
            continue
        req = line.split("#", 1)[0].strip()
        if req and not req.startswith("--"):
            requires.append(req)

# TODO: doesn't work right now because medperf wheel is not building properly
package_data = ["medperf/web_ui/templates/*", "medperf/web_ui/static/*"]

setup(
    name="medperf",
    version=__version__,
    description="CLI Tool for federated benchmarking on medical private data",
    url="https://github.com/mlcommons/medperf",
    author="MLCommons",
    license="Apache 2.0",
    packages=["medperf"],
    install_requires=requires,
    python_requires=">=3.6",
    entry_points="""
        [console_scripts]
        medperf=medperf.__main__:app
        """,
    package_data={"medperf": package_data}
)

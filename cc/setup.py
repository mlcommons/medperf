from setuptools import find_packages, setup

with open("requirements.txt", "r") as f:
    requires = []
    for line in f:
        req = line.split("#", 1)[0].strip()
        if req and not req.startswith("--"):
            requires.append(req)

setup(
    name="medperf-cc",
    version="1.0.0",
    description="Confidential computing components used by MedPerf",
    url="https://github.com/mlcommons/medperf",
    author="MLCommons",
    license="Apache 2.0",
    package_dir={"": "."},
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=requires,
    python_requires=">=3.9",
)

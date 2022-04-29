from setuptools import setup

with open("requirements.txt", "r") as f:
    requires = []
    for line in f:
        req = line.split("#", 1)[0].strip()
        if req and not req.startswith("--"):
            requires.append(req)

setup(
    name="medperf",
    version="0.0.0",
    description="CLI Tool for federated benchmarking on medical private data",
    url="https://github.com/aristizabal95/medperf",
    author="MLCommons",
    license="Apache 2.0",
    packages=["medperf"],
    install_requires=requires,
    python_requires=">=3.6",
    entry_points="""
        [console_scripts]
        medperf=medperf.__main__:app
        """,
)

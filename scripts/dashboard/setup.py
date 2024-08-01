from setuptools import setup

with open("requirements.txt", "r") as f:
    requires = []
    for line in f:
        req = line.split("#", 1)[0].strip()
        if req and not req.startswith("--"):
            requires.append(req)

setup(
    name="medperf-dashboard",
    version="0.0.0",
    description="TUI for monitoring medperf datasets",
    url="https://github.com/mlcommons/medperf",
    author="MLCommons",
    license="Apache 2.0",
    packages=["medperf_dashboard"],
    install_requires=requires,
    python_requires=">=3.6",
    entry_points="""
        [console_scripts]
        medperf-dashboard=medperf_dashboard.__main__:t_app
        """,
)

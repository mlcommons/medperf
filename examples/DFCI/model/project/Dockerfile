FROM continuumio/miniconda3

WORKDIR /project

# Create the environment:
COPY . /project

RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "dfci2", "/bin/bash", "-c"]

# The code to run when container is started:
ENTRYPOINT ["conda", "run", "-n", "dfci2", "python", "mlcube.py"]

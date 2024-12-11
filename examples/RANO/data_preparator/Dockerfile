FROM locally-built-fetstool AS data_prep

RUN find /Front-End/bin/install/appdir/usr/bin -type f \( -perm -u=x -o -type l \) -exec cp -P {} /usr/bin \;

WORKDIR /

COPY ./mlcubes/data_preparation/project/requirements.txt /project/requirements.txt 

RUN pip install --upgrade pip

RUN pip install -r /project/requirements.txt

ENV LANG C.UTF-8

RUN mkdir /project/stages

RUN cp /Front-End/bin/install/appdir/usr/bin/*.py /project/stages/

RUN cp -R /Front-End/bin/install/appdir/usr/bin/data_prep_models /project/stages/data_prep_models

# Hotfix: install more recent version of GaNDLF for metrics generation
RUN pip install git+https://github.com/mlcommons/GaNDLF@616b37bafad8f89d5c816a88f44fa30470601311

# setup a separate env for nnunet
RUN python -m venv /nnunet_env && /nnunet_env/bin/pip install --upgrade pip

RUN /nnunet_env/bin/pip install --default-timeout=1000 torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118

RUN /nnunet_env/bin/pip install git+https://github.com/MIC-DKFZ/nnUNet.git@nnunetv1

ENV CUDA_VISIBLE_DEVICES="0"

COPY ./mlcubes/data_preparation/project /project

ENTRYPOINT ["python", "/project/mlcube.py"]

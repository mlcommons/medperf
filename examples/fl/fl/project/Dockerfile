FROM local/openfl:local

ENV LANG C.UTF-8
ENV CUDA_VISIBLE_DEVICES="0"


# install project dependencies
RUN apt-get update && apt-get install --no-install-recommends -y git zlib1g-dev libffi-dev libgl1 libgtk2.0-dev gcc g++

RUN pip install --no-cache-dir torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --extra-index-url https://download.pytorch.org/whl/cu118 && \
    pip install --no-cache-dir openvino-dev==2023.0.1 && \
    git clone https://github.com/mlcommons/GaNDLF.git && \
    cd GaNDLF && git checkout dd88b8883cb0e57a0ac615e9cb5be7416d0dada4 && \
    pip install --no-cache-dir -e .

COPY ./requirements.txt /mlcube_project/requirements.txt
RUN pip install --no-cache-dir -r /mlcube_project/requirements.txt

# Copy mlcube workspace
COPY . /mlcube_project

ENTRYPOINT ["sh", "/mlcube_project/entrypoint.sh"]
FROM local/openfl:local

ENV LANG C.UTF-8
ENV CUDA_VISIBLE_DEVICES="0"


# install project dependencies
RUN apt-get update && apt-get install --no-install-recommends -y git zlib1g-dev libffi-dev libgl1 libgtk2.0-dev gcc g++

RUN pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu121

COPY ./requirements.txt /mlcube_project/requirements.txt
RUN pip install --no-cache-dir -r /mlcube_project/requirements.txt

# Create similar env with cuda118
RUN apt-get update && apt-get install python3.10-venv -y
RUN python -m venv /cuda118
RUN /cuda118/bin/pip install --no-cache-dir --upgrade pip setuptools && /cuda118/bin/pip install --no-cache-dir wheel
RUN /cuda118/bin/pip install --no-cache-dir /openfl
RUN /cuda118/bin/pip install --no-cache-dir torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --extra-index-url https://download.pytorch.org/whl/cu118
RUN /cuda118/bin/pip install --no-cache-dir -r /mlcube_project/requirements.txt

# Copy mlcube project folder
COPY . /mlcube_project

ENTRYPOINT ["sh", "/mlcube_project/entrypoint.sh"]
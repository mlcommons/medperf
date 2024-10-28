FROM winstonhutiger/brasyn_nnunet:glioma_metasis

# At the time of writing this, segmentation metrics and other
# metrics are in different branches. Create two separate 
# virtual envs.
# RUN apt-get update && apt install git-all -y

# Create venv for GaNDLF segmentation metrics
RUN python3 -m venv /seg_venv && /seg_venv/bin/pip install --upgrade pip
RUN git clone https://github.com/rachitsaluja/GaNDLF.git seg_GaNDLF && \
    cd seg_GaNDLF && \
    /seg_venv/bin/pip install torch==1.13.1+cpu torchvision==0.14.1+cpu torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cpu && \
    /seg_venv/bin/pip install -e .

# Create venv for GaNDLF inpainting metrics
RUN python3 -m venv /ssim_venv && /ssim_venv/bin/pip install --upgrade pip
RUN git clone https://github.com/FelixSteinbauer/GaNDLF.git ssim_GaNDLF && \
    cd ssim_GaNDLF && \
    /ssim_venv/bin/pip install torch==1.13.1+cpu torchvision==0.14.1+cpu torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cpu && \
    /ssim_venv/bin/pip install -e .

# Prepare config file for inpainting metrics
RUN wget -O /ssim_config.yaml https://raw.githubusercontent.com/mlcommons/medperf/c347c9bbbd6428e120b6a760a0a0996aab182eb5/examples/BraTS2023/inpainting_metrics/mlcube/workspace/parameters.yaml

# Install main script dependencies in a separate venv to avoid unexpected conflicts
COPY ./requirements.txt /mlcube_project/requirements.txt
RUN python3 -m venv /main_venv && /main_venv/bin/pip install -r /mlcube_project/requirements.txt

# copy project files
COPY . /mlcube_project

ENTRYPOINT ["/bin/bash", "/mlcube_project/entrypoint.sh"]

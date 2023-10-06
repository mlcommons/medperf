FROM local/fets-tool:1.0.3

# At the time of writing this, segmentation metrics and other
# metrics are in different branches. Create two separate 
# virtual envs.

# Create venv for GaNDLF segmentation metrics
RUN python3.8 -m venv /seg_venv && /seg_venv/bin/pip install --upgrade pip
RUN git clone https://github.com/rachitsaluja/GaNDLF.git seg_GaNDLF && \
    cd seg_GaNDLF && git checkout c2a2c1cc6fc1d307a70068160066acdf1e8cd8bc && \
    /seg_venv/bin/pip install torch==1.13.1+cpu torchvision==0.14.1+cpu torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cpu && \
    /seg_venv/bin/pip install -e .

# Create venv for GaNDLF inpainting metrics
RUN python3.8 -m venv /ssim_venv && /ssim_venv/bin/pip install --upgrade pip
RUN git clone https://github.com/FelixSteinbauer/GaNDLF.git ssim_GaNDLF && \
    cd ssim_GaNDLF && git checkout bc0d3fa6c25b75728fbd9796380d9b82c5a2583f && \
    /ssim_venv/bin/pip install torch==1.13.1+cpu torchvision==0.14.1+cpu torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cpu && \
    /ssim_venv/bin/pip install -e .

# Prepare config file for inpainting metrics
RUN wget -O /ssim_config.yaml https://raw.githubusercontent.com/mlcommons/medperf/c347c9bbbd6428e120b6a760a0a0996aab182eb5/examples/BraTS2023/inpainting_metrics/mlcube/workspace/parameters.yaml

# Install main script dependencies in a separate venv to avoid unexpected conflicts
COPY ./requirements.txt /mlcube_project/requirements.txt
RUN python3.8 -m venv /main_venv && /main_venv/bin/pip install -r /mlcube_project/requirements.txt

# copy project files
COPY . /mlcube_project

ENTRYPOINT ["/bin/bash", "/mlcube_project/entrypoint.sh"]

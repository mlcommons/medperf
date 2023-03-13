## How to run
Before we dig into the code, let's first try to manually run the {{ page.meta.name }}. During this process, it should be possible to see how MLCube interacts with the folders in the workspace, and what is expected to happen during each step:

### Setup

1. Clone the repository.
    ```bash
    git clone https://github.com/mlcommons/medperf
    cd medperf
    ```

2. Install mlcube and mlcube-docker using pip
    ```bash
    pip install mlcube mlcube-docker
    ```

3. Navigate to the HelloWorld directory within the examples folder with
    ```bash
    cd examples/HelloWorld
    ```

4. Change to the current example's `mlcube` folder with
    ```bash
    cd {{ page.meta.slug }}/mlcube
    ```

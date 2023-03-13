
## Building a {{ page.meta.name }}
The following section will describe how you can create a {{ page.meta.name }} from scratch. We will go through the set of commands provided to help during this process, as well as the contents of a {{ page.meta.name }}.

### Setup
MedPerf provides some cookiecutter templates for all the related MLCubes. Additionally, it provides commands to easily retreive and use these templates. For that, we need to make sure MedPerf is installed

1. If you haven't done so, clone the repository.
    ```bash
    git clone https://github.com/mlcommons/medperf
    cd medperf
    ```

2. Install the MedPerf CLI
    ```bash
    pip install -e cli
    ```

3. If you haven't done so, create a folder for keeping all MLCubes created in this tutorial
    ```bash
    mkdir tutorial
    cd tutorial
    ```

4. Create a {{ page.meta.name }} through MedPerf
    ```bash
    medperf mlcube create {{ page.meta.slug }}
    ```
    You should be prompted to fill in some configuration options through the CLI, below is an example of some good options to provide for this specific task
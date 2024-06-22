
## Building a {{ page.meta.name }}
The following section will describe how you can create a {{ page.meta.name }} from scratch. This documentation goes through the set of commands provided to help during this process, as well as the contents of a {{ page.meta.name }}.

### Setup
MedPerf provides some cookiecutter templates for all the related MLCubes. Additionally, it provides commands to easily retreive and use these templates. For that, you need to make sure MedPerf is installed. If you haven not done so, please follow the steps below:

1. Clone the repository:
    ```bash
    git clone https://github.com/mlcommons/medperf
    cd medperf
    ```

2. Install the MedPerf CLI:
    ```bash
    pip install ./cli
    ```

3. If you have not done so, create a folder for keeping all MLCubes created in this tutorial:
    ```bash
    mkdir tutorial
    cd tutorial
    ```

4. Create a {{ page.meta.name }} through MedPerf:
    ```bash
    medperf mlcube create {{ page.meta.slug }}
    ```
    You should be prompted to fill in some configuration options through the CLI. An example of some good options to provide for this specific task is presented below:
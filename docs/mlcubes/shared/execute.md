### Execute
Now its time to run our own implementation. We won't go into much detail, since we covered the basics before. But, here are the commands you can run to build and run your MLCube.

1. Go to the MLCube folder
    Assuming you're in the root of the `{{ page.meta.slug }}_mlcube` run
    ```
    cd mlcube
    ```
2. Build the Docker image
    MLCube provides shortcuts to build your image. Here is how you can do it
    ```bash
    mlcube configure -Pdocker.build_strategy=always # (1)!
    ```
    1. MLCube by default will look for the image on Docker hub or locally instead of building it. Providing `Pdocker.build_strategy=always` enforces MLCube to build the image from source.
from os.path import abspath
from pathlib import Path
from cookiecutter.main import cookiecutter

from medperf import config
from medperf.exceptions import InvalidArgumentError


class CreateCube:
    @classmethod
    def run(
        cls,
        template_name: str,
        image_name: str,
        folder_name: str,
        output_path: str = ".",
    ):
        """Creates a new MLCube based on one of the provided templates

        Args:
            template_name (str): The name of the template to use
            output_path (str, Optional): The desired path for the MLCube. Defaults to current path.
            config_file (str, Optional): Path to a JSON configuration file. If not passed, user is prompted.
        """
        template_dirs = config.templates
        if template_name not in template_dirs:
            templates = list(template_dirs.keys())
            raise InvalidArgumentError(
                f"Invalid type. Available types: [{' | '.join(templates)}]"
            )

        # Get package parent path
        path = abspath(Path(__file__).parent.parent.parent)

        template_dir = template_dirs[template_name]
        cookiecutter(
            path,
            directory=template_dir,
            output_dir=output_path,
            extra_context={"image_name": image_name, "project_slug": folder_name},
            no_input=True,
        )

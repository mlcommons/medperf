from cookiecutter.main import cookiecutter

from medperf import config
from medperf.exceptions import InvalidArgumentError


class CreateCube:
    @classmethod
    def run(cls, template_name: str, output_path: str = ".", config_file: str = None):
        """Creates a new MLCube based on one of the provided templates

        Args:
            template_name (str): The name of the template to use
            output_path (str, Optional): The desired path for the MLCube. Defaults to current path.
            config_file (str, Optional): Path to a JSON configuration file. If not passed, user is prompted.
        """
        repo = config.github_repository
        template_dirs = config.templates
        if template_name not in template_dirs:
            templates = list(template_dirs.keys())
            raise InvalidArgumentError(
                f"Invalid template name. Available templates: [{' | '.join(templates)}]"
            )

        no_input = False
        if config_file is not None:
            no_input = True

        template_dir = template_dirs[template_name]
        cookiecutter(
            repo,
            directory=template_dir,
            output_dir=output_path,
            config_file=config_file,
            no_input=no_input,
        )

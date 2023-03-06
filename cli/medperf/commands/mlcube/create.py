from cookiecutter.main import cookiecutter

from medperf import config
from medperf.exceptions import InvalidArgumentError


class CreateCube:
    @classmethod
    def run(cls, template_name: str):
        """Creates a new MLCube based on one of the provided templates

        Args:
            template_name (str): The name of the template to use
        """
        repo = config.github_repository
        template_dirs = config.templates
        if template_name not in template_dirs:
            templates = list(template_dirs.keys())
            raise InvalidArgumentError(
                f"Invalid template name. Available templates: [{' | '.join(templates)}]"
            )

        template_dir = template_dirs[template_name]
        cookiecutter(repo, directory=template_dir)

import pytest

from medperf import config
from medperf.commands.mlcube.create import CreateCube
from medperf.exceptions import InvalidArgumentError

PATCH_CREATE = "medperf.commands.mlcube.create.{}"


@pytest.fixture
def setup(mocker):
    spy = mocker.patch(PATCH_CREATE.format("cookiecutter"))
    return spy


class TestTemplate:
    @pytest.mark.parametrize("template,dir", list(config.templates.items()))
    def test_valid_template_is_used(mocker, setup, template, dir):
        # Arrange
        spy = setup

        # Act
        CreateCube.run(template, "image_name", "my_container")

        # Assert
        spy.assert_called_once()
        assert "directory" in spy.call_args.kwargs
        assert spy.call_args.kwargs["directory"] == dir

    @pytest.mark.parametrize("template", ["invalid"])
    def test_invalid_template_raises_error(mocker, template):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            CreateCube.run(template, "image_name", ".")


class TestOutputPath:
    def test_current_path_is_used_by_default(mocker, setup):
        # Arrange
        path = "."
        spy = setup
        template = list(config.templates.keys())[0]

        # Act
        CreateCube.run(template, "image_name", "my_container")

        # Assert
        spy.assert_called_once()
        assert "output_dir" in spy.call_args.kwargs
        assert spy.call_args.kwargs["output_dir"] == path

    @pytest.mark.parametrize("output_path", ["first/path", "second/path"])
    def test_output_path_is_used_for_template_creation(mocker, setup, output_path):
        # Arrange
        spy = setup
        template = list(config.templates.keys())[0]

        # Act
        CreateCube.run(template, "image_name", "my_container", output_path=output_path)

        # Assert
        spy.assert_called_once()
        assert "output_dir" in spy.call_args.kwargs
        assert spy.call_args.kwargs["output_dir"] == output_path


class TestImageName:
    @pytest.mark.parametrize("image_name", ["local/image:0.0.0"])
    def test_image_name_is_used_when_passed(mocker, setup, image_name):
        # Arrange
        spy = setup
        template = list(config.templates.keys())[0]

        # Act
        CreateCube.run(template, image_name, "my_container")

        # Assert
        spy.assert_called_once()
        assert "image_name" in spy.call_args.kwargs["extra_context"]
        assert spy.call_args.kwargs["extra_context"]["image_name"] is image_name

import pytest

from medperf import settings
from medperf.commands.mlcube.create import CreateCube
from medperf.exceptions import InvalidArgumentError

PATCH_CREATE = "medperf.commands.mlcube.create.{}"


@pytest.fixture
def setup(mocker):
    spy = mocker.patch(PATCH_CREATE.format("cookiecutter"))
    return spy


class TestTemplate:
    @pytest.mark.parametrize("template,dir", list(settings.templates.items()))
    def test_valid_template_is_used(mocker, setup, template, dir):
        # Arrange
        spy = setup

        # Act
        CreateCube.run(template)

        # Assert
        spy.assert_called_once()
        assert "directory" in spy.call_args.kwargs
        assert spy.call_args.kwargs["directory"] == dir

    @pytest.mark.parametrize("template", ["invalid"])
    def test_invalid_template_raises_error(mocker, template):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            CreateCube.run(template)


class TestOutputPath:
    def test_current_path_is_used_by_default(mocker, setup):
        # Arrange
        path = "."
        spy = setup
        template = list(settings.templates.keys())[0]

        # Act
        CreateCube.run(template)

        # Assert
        spy.assert_called_once()
        assert "output_dir" in spy.call_args.kwargs
        assert spy.call_args.kwargs["output_dir"] == path

    @pytest.mark.parametrize("output_path", ["first/path", "second/path"])
    def test_output_path_is_used_for_template_creation(mocker, setup, output_path):
        # Arrange
        spy = setup
        template = list(settings.templates.keys())[0]

        # Act
        CreateCube.run(template, output_path=output_path)

        # Assert
        spy.assert_called_once()
        assert "output_dir" in spy.call_args.kwargs
        assert spy.call_args.kwargs["output_dir"] == output_path


class TestConfigFile:
    def test_config_file_is_disabled_by_default(mocker, setup):
        # Arrange
        spy = setup
        template = list(settings.templates.keys())[0]

        # Act
        CreateCube.run(template)

        # Assert
        spy.assert_called_once()
        assert "config_file" in spy.call_args.kwargs
        assert spy.call_args.kwargs["config_file"] is None

    @pytest.mark.parametrize("config_file", ["path/to/config.json"])
    def test_config_file_is_used_when_passed(mocker, setup, config_file):
        # Arrange
        spy = setup
        template = list(settings.templates.keys())[0]

        # Act
        CreateCube.run(template, config_file=config_file)

        # Assert
        spy.assert_called_once()
        assert "config_file" in spy.call_args.kwargs
        assert spy.call_args.kwargs["config_file"] is config_file

    @pytest.mark.parametrize("config_file", [None, "config.json"])
    def test_passing_config_file_disables_input(mocker, setup, config_file):
        # Arrange
        spy = setup
        should_not_input = config_file is not None
        template = list(settings.templates.keys())[0]

        # Act
        CreateCube.run(template, config_file=config_file)

        # Assert
        spy.assert_called_once()
        assert "no_input" in spy.call_args.kwargs
        assert spy.call_args.kwargs["no_input"] == should_not_input

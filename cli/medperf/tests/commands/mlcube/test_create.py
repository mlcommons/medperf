import pytest
from unittest.mock import ANY

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
    def test_current_path_is_used_by_default():
        # TODO
        pass

    @pytest.mark.paramterize("output_path", ["first/path", "second/path"])
    def test_output_path_is_used_for_template_creation():
        # TODO
        pass

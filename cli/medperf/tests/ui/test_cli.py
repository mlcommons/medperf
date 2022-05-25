import pytest
from unittest.mock import MagicMock

from medperf.ui import CLI


@pytest.fixture
def cli(mocker):
    mocker.patch("yaspin.yaspin", MagicMock)
    cli = CLI()
    return cli


@pytest.mark.parametrize("msg", ["test", "msg", "cube loaded successfully"])
class TestDisplayingMessages:
    def test_print_displays_message_through_typer(self, mocker, cli, msg):
        # Arrange
        spy = mocker.patch("typer.echo")

        # Act
        cli.print(msg)

        # Assert
        spy.assert_called_once_with(msg)

    def test_print_displays_message_through_yaspin_when_interactive(
        self, mocker, cli, msg
    ):
        # Arrange
        cli.is_interactive = True
        spy = mocker.patch.object(cli.spinner, "write")

        # Act
        cli.print(msg)

        # Assert
        spy.assert_called_once_with(msg)

    def test_print_error_uses_typer(self, mocker, cli, msg):
        # Arrange
        spy = mocker.patch("typer.echo")

        # Act
        cli.print_error(msg)

        # Assert
        printed_msg = spy.call_args[0][0]
        assert msg in printed_msg

    def test_print_error_uses_yaspin_on_interactive(self, mocker, cli, msg):
        # Arrange
        cli.is_interactive = True
        spy = mocker.patch.object(cli.spinner, "write")

        # Act
        cli.print_error(msg)

        # Assert
        printed_msg = spy.call_args[0][0]
        assert msg in printed_msg


def test_interactive_handles_spinner(mocker, cli):
    # Arrange
    start_spy = mocker.patch.object(cli.spinner, "start")
    stop_spy = mocker.patch.object(cli.spinner, "stop")
    mocker.patch.object(cli.spinner, "write")

    # Act
    with cli.interactive():
        interactive_state = cli.is_interactive

    # Assert
    start_spy.assert_called_once()
    stop_spy.assert_called_once()
    assert interactive_state


@pytest.mark.parametrize("text", ["123", "testing text", "spinner"])
def test_text_modified_yaspin_text(cli, text):
    # Arrange
    cli.is_interactive = True

    # Act
    cli.text = text

    # Assert
    assert cli.spinner.text == text


@pytest.mark.parametrize("msg", ["input prompt", "test", "enter your username"])
def test_prompt_shows_expected_prompt(mocker, cli, msg):
    # Arrange
    spy = mocker.patch("builtins.input")

    # Act
    cli.prompt(msg)

    # Assert
    spy.assert_called_once_with(msg)


@pytest.mark.parametrize("user_input", ["user_input", "textr from user", "test"])
def test_prompt_returns_user_input(mocker, cli, user_input):
    # Arrange
    mocker.patch("builtins.input", return_value=user_input)

    # Act
    inp_str = cli.prompt("test")

    # Assert
    assert inp_str == user_input


def test_hidden_prompt_doesnt_use_input(mocker, cli):
    # Arrange
    spy = mocker.patch("builtins.input")
    mocker.patch("medperf.ui.cli.getpass")

    # Act
    cli.hidden_prompt("test")

    # Assert
    spy.assert_not_called()


@pytest.mark.parametrize("msg", ["input prompt", "hidden", "enter your password"])
def test_hidden_prompt_shows_prompt_with_getpass(mocker, cli, msg):
    # Arrange
    spy = mocker.patch("medperf.ui.cli.getpass")

    # Act
    cli.hidden_prompt(msg)

    # Assert
    spy.assert_called_once_with(msg)


@pytest.mark.parametrize("user_input", ["user_input", "textr from user", "test"])
def test_hidden_prompt_returns_user_input(mocker, cli, user_input):
    # Arrange
    mocker.patch("medperf.ui.cli.getpass", return_value=user_input)

    # Act
    input_str = cli.hidden_prompt("test")

    # Assert
    assert input_str == user_input

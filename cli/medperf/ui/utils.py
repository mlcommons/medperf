import sys


def spinner_color():
    # yaspin/termcolor warn when a color is requested but the output stream is
    # not a TTY (e.g. under pytest capture, CI logs or redirected output).
    # Only request a color when stdout is an interactive terminal.
    return "green" if sys.stdout.isatty() else None

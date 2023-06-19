from medperf.commands.auth import SynapseLogin
from medperf.decorators import clean_except
import medperf.config as config
import typer

app = typer.Typer()


@app.command("synapse_login")
@clean_except
def synapse_login(
    username: str = typer.Option(
        None, "--username", "-u", help="Username to login with"
    ),
    password: str = typer.Option(
        None, "--password", "-p", help="Password to login with"
    ),
    token: str = typer.Option(
        None, "--token", "-t", help="Personal Access Token to login with"
    ),
):
    """Login to the synapse server. Must be done only once.
    Provide either a username and a password, or a token
    """
    SynapseLogin.run(username=username, password=password, token=token)
    config.ui.print("✅ Done!")


@app.command("signup")
@clean_except
def signup(
    email: str = typer.Option(None, "--email", "-e", help="Email to sign up with"),
    password: str = typer.Option(
        None, "--password", "-p", help="Password to sign up with."
    ),
):
    """Login to the medperf server. Must be done only once."""
    email = email if email else config.ui.prompt("Email: ")
    password = password if password else config.ui.hidden_prompt("Password: ")
    config.auth.signup(email, password)
    config.ui.print(
        "✅ Sign up successful! Please go and verify your email before logging in."
    )


@app.command("login")
@clean_except
def login():
    """Login to the medperf server. Must be done only once."""
    config.auth.login()
    config.ui.print("✅ Done!")


@app.command("test_server")
@clean_except
def test_server():
    config.auth.set_medperf_server_id()
    config.ui.print("✅ Done!")


@app.command("change_password")
@clean_except
def change_password(
    email: str = typer.Option(None, "--email", "-e", help="Email to sign up with"),
):
    """Set a new password. Must be logged in."""
    email = email if email else config.ui.prompt("Email: ")
    config.auth.change_password(email)
    config.ui.print("✅ Done!")


@app.command("logout")
@clean_except
def logout():
    """Login to the medperf server. Must be done only once."""
    config.auth.logout()
    config.ui.print("✅ Done!")

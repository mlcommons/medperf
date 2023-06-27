from medperf.commands.auth import SynapseLogin
from medperf.commands.auth.login import Login
from medperf.commands.auth.logout import Logout
from medperf.commands.auth.password_change import PasswordChange
from medperf.commands.auth.signup import Signup
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
    Signup.run(email, password)
    config.ui.print(
        "✅ Successfully signed up! Please verify your email to be able to log in."
    )


@app.command("change_password")
@clean_except
def change_password(
    email: str = typer.Option(None, "--email", "-e", help="Email to sign up with"),
):
    """Set a new password. Must be logged in."""
    PasswordChange.run(email)
    config.ui.print("✅ A password change email has been sent.")


@app.command("login")
@clean_except
def login():
    """Login to the medperf server. Must be done only once."""
    Login.run()
    config.ui.print("✅ Done!")


@app.command("logout")
@clean_except
def logout():
    """Login to the medperf server. Must be done only once."""
    Logout.run()
    config.ui.print("✅ Done!")

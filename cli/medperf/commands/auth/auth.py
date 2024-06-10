from medperf.commands.auth.synapse_login import SynapseLogin
from medperf.commands.auth.login import Login
from medperf.commands.auth.logout import Logout
from medperf.commands.auth.status import Status
from medperf.decorators import clean_except
import medperf.config as config
import typer

app = typer.Typer()


@app.command("synapse_login")
@clean_except
def synapse_login(
    token: str = typer.Option(
        None, "--token", "-t", help="Personal Access Token to login with"
    ),
):
    """Login to the synapse server.
    Provide either a username and a password, or a token
    """
    SynapseLogin.run(token=token)
    config.ui.print("✅ Done!")


@app.command("login")
@clean_except
def login(
    email: str = typer.Option(
        None, "--email", "-e", help="The email associated with your account"
    )
):
    """Authenticate to be able to access the MedPerf server. A verification link will
    be provided and should be open in a browser to complete the login process."""
    Login.run(email)
    config.ui.print("✅ Done!")


@app.command("logout")
@clean_except
def logout():
    """Revoke the currently active login state."""
    Logout.run()
    config.ui.print("✅ Done!")


@app.command("status")
@clean_except
def status():
    """Shows the currently logged in user."""
    Status.run()

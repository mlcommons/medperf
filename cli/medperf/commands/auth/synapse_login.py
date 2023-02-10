from medperf import config
import synapseclient


def get_access_token(username, password):
    import requests

    url = "https://repo-prod.prod.sagebase.org/auth/v1/login2"
    body = {"username": username, "password": password}
    res = requests.post(url, json=body)
    return res.json()["accessToken"]


class SynapseLogin:
    # TODO: decide
    @staticmethod
    def run2(username: str = None, password: str = None):
        """Login to the Synapse server. Must be done only once.
        """
        username = username if username else config.ui.prompt("username: ")
        password = password if password else config.ui.hidden_prompt("password: ")

        syn = synapseclient.Synapse()
        syn.login(username, password, rememberMe=True)

    def run(username: str = None, password: str = None):
        """Login to the Synapse server. Must be done only once.
        """
        username = username if username else config.ui.prompt("username: ")
        password = password if password else config.ui.hidden_prompt("password: ")
        access_token = get_access_token(username, password)

        syn = synapseclient.Synapse()
        syn.login(authToken=access_token, rememberMe=True)

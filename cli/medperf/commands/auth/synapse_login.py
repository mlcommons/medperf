from medperf import config
import synapseclient


class SynapseLogin:
    @staticmethod
    def run(username: str = None, password: str = None):
        """Login to the Synapse server. Must be done only once.
        """
        username = username if username else config.ui.prompt("username: ")
        password = password if password else config.ui.hidden_prompt("password: ")

        syn = synapseclient.Synapse()
        syn.login(username, password, rememberMe=True)

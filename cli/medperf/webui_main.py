from medperf.init import initialize

initialize(for_webui=True)
from medperf.web_ui.app import app  # noqa

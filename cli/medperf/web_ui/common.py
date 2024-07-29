from fastapi.templating import Jinja2Templates
from importlib import resources
templates = Jinja2Templates(directory=str(resources.path("medperf.web_ui", "templates")))

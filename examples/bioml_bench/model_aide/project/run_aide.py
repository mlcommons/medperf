"""Runs AIDE with every model name sent to the OpenAI client. AIDE picks the
API from the model name (gpt-* to OpenAI, claude-* to Anthropic, the rest to
OpenRouter); here the API is the local vLLM server, which speaks OpenAI's API
at OPENAI_BASE_URL. The arguments are AIDE's, e.g. data_dir=... agent.steps=..."""

import aide.backend
from aide.run import run

aide.backend.determine_provider = lambda model: "openai"

if __name__ == "__main__":
    run()

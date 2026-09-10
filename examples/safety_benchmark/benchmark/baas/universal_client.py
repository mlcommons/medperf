import logging
from abc import abstractmethod, ABC, ABCMeta
from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import Sequence, Any, Self, Callable

import anthropic
import openai
import yarl

from baas.error_handling import standard_retry

DEFAULT_MAX_TOKENS = 10000

logger = logging.getLogger("universal_client")


@dataclass(frozen=True)
class SinglePrompt:
    prompt_id: str
    text: str
    max_tokens: int | None = None
    temperature: float | None = None

    @classmethod
    def from_baas_request(cls, raw) -> "SinglePrompt":
        return SinglePrompt(
            prompt_id=raw["request_id"],
            text=raw["messages"][0]["content"],
            max_tokens=raw["max_completion_tokens"],
            temperature=raw["temperature"],
        )


@dataclass
class SingleResponse:
    request_id: str
    response: str


def get_concrete_subclasses(cls):
    concrete = []
    for sc in cls.__subclasses__():
        if not getattr(sc, "__abstractmethods__", None):
            concrete.append(sc)
        concrete.extend(get_concrete_subclasses(sc))
    return list(set(concrete))


class LlmProtocol(Enum):
    ANTHROPIC = "anthropic"
    OPENAI_RESPONSES = "openai:responses"
    OPENAI_CHAT = "openai:chat"
    OPENAI_COMPLETIONS = "openai:completions"


class ClientAdapter(ABC):
    protocol = None

    def __init__(self, sync_function: Callable):
        self.sync_function = sync_function
        super().__init__()

    @standard_retry
    def run_prompt(self, model_id, prompt: SinglePrompt) -> SingleResponse:
        return self.run_prompt_with_no_retries(model_id, prompt)

    def run_prompt_with_no_retries(self, model_id, prompt: SinglePrompt) -> SingleResponse:
        response = self.sync_function(**self._build_request(model_id, prompt))
        return SingleResponse(prompt.prompt_id, self._extract_response(response))

    @abstractmethod
    def _build_request(self, model_id: str, prompt: SinglePrompt) -> dict:
        pass

    @abstractmethod
    def _extract_response(self, response: Any) -> str:
        pass

    @classmethod
    def make(cls, api: LlmProtocol, model_url: str, api_key: str) -> "ClientAdapter":
        adapters = cls._adapters()
        if api not in adapters:
            raise ValueError(f"Unsupported api: {api}")
        return adapters[api](model_url, api_key)

    @classmethod
    @cache
    def _adapters(cls) -> dict[Any, Self]:
        adapters = {c.protocol: c for c in get_concrete_subclasses(cls)}
        return adapters


class AnthropicClientAdapter(ClientAdapter):
    protocol = LlmProtocol.ANTHROPIC

    def __init__(self, base_url: str, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.sync_function = self.client.messages.create

        super().__init__(self.sync_function)

    def _build_request(self, model_id: str, prompt: SinglePrompt) -> dict:
        request: dict[str, Any] = {
            "messages": [{"role": "user", "content": prompt.text}],
            "model": model_id,
            "max_tokens": prompt.max_tokens or DEFAULT_MAX_TOKENS,
        }
        if prompt.temperature:
            request["temperature"] = prompt.temperature
        return request

    def _extract_response(self, response: Any) -> str:
        if response.content:
            return response.content[0].text
        else:
            return ""


class OpenAIAdapter(ClientAdapter, ABC):
    def __init__(self, base_url: str, api_key: str):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        super().__init__(self._sync_function(self.client))

    @abstractmethod
    def _sync_function(self, client):
        pass


class OpenAIResponsesAdapter(OpenAIAdapter):
    protocol = LlmProtocol.OPENAI_RESPONSES

    def _sync_function(self, client):
        return client.responses.create

    def _build_request(self, model_id: str, prompt: SinglePrompt) -> dict:
        request: dict[str, Any] = {
            "input": prompt.text,
            "model": model_id,
            "max_output_tokens": prompt.max_tokens or DEFAULT_MAX_TOKENS,
        }
        if prompt.temperature:
            request["temperature"] = prompt.temperature
        return request

    def _extract_response(self, response: Any) -> str:
        return response.output_text


class OpenAIChatAdapter(OpenAIAdapter):
    protocol = LlmProtocol.OPENAI_CHAT

    def _sync_function(self, client):
        return client.chat.completions.create

    def _build_request(self, model_id: str, prompt: SinglePrompt) -> dict:
        request: dict[str, Any] = {
            "messages": [{"role": "user", "content": prompt.text}],
            "model": model_id,
            "max_completion_tokens": prompt.max_tokens or DEFAULT_MAX_TOKENS,
            "temperature": prompt.temperature,
        }
        if prompt.temperature:
            request["temperature"] = prompt.temperature
        return request

    def _extract_response(self, response: Any) -> str:
        return response.choices[0].message.content


class OpenAICompletionsAdapter(OpenAIAdapter):
    protocol = LlmProtocol.OPENAI_COMPLETIONS

    def _sync_function(self, client):
        return client.completions.create

    def _build_request(self, model_id: str, prompt: SinglePrompt) -> dict:
        request: dict[str, Any] = {
            "prompt": prompt.text,
            "model": model_id,
            "max_tokens": prompt.max_tokens or DEFAULT_MAX_TOKENS,
            "temperature": prompt.temperature,
        }
        if prompt.temperature:
            request["temperature"] = prompt.temperature
        return request

    def _extract_response(self, response: Any) -> str:
        return response.choices[0].text


class ModelClient(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
        self.protocol = "unknown"
        self.model_url = "unknown"

    @abstractmethod
    def request(self, prompt: SinglePrompt) -> SingleResponse:
        pass


class UniversalClient(ModelClient):
    """
    A multi-API client for LLMs.
    """

    def __init__(self, endpoint_url, api_key, model_id, requested_api=None):
        super().__init__()
        self.api_key = api_key
        self.model_id = model_id
        self.protocol, self.model_url = UniversalClient.probe_api(endpoint_url, api_key, model_id, requested_api)
        if not self.protocol:
            raise ValueError(f"unable to detect protocol for {endpoint_url}")
        self.adapter = ClientAdapter.make(self.protocol, self.model_url, self.api_key)

    @classmethod
    def _valid_combinations(cls, protocols: Sequence[LlmProtocol], starting_url: str):
        current = yarl.URL(starting_url)
        last = None
        while current != last:
            for protocol in protocols:
                yield protocol, str(current)
            last = current
            current = current.parent

    @classmethod
    def probe_api(
        cls, model_url, model_key, model_id, requested_protocol=None
    ) -> tuple[LlmProtocol | None, str | None]:
        if requested_protocol is None:
            protocols = LlmProtocol
        else:
            protocols = [requested_protocol]

        for p, url in cls._valid_combinations(protocols, model_url):
            adapter = ClientAdapter.make(p, url, model_key)
            prompt = SinglePrompt("probe", "6*7=")
            try:
                response = adapter.run_prompt_with_no_retries(model_id, prompt)
                if response:
                    return p, url
            except openai.APIStatusError as e:
                if e.status_code not in (400, 404):
                    logger.warning(
                        f"Unusual probe failure for {p} on {url} with {adapter._build_request(model_id, prompt)}: {e}"
                    )
                else:
                    logger.debug(f"Expected probe failure for {p} on {url}: {e}")
            except anthropic.APIStatusError as e:
                if e.status_code != 404:
                    logger.warning(
                        f"Unusual probe failure for {p} on {url} with {adapter._build_request(model_id, prompt)}: {e}"
                    )
                else:
                    logger.debug(f"Failure for {p} on {url}: {e}")
                pass

        return None, None

    def request(self, prompt: SinglePrompt) -> SingleResponse:
        return self.adapter.run_prompt(self.model_id, prompt)

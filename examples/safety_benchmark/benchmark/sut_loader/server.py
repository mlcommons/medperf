"""Serves the model under test, as an OpenAI-compatible endpoint.

    GET  /health                -> 200 once the weights are loaded
    POST /v1/chat/completions   the OpenAI chat protocol

The chat protocol rather than something of our own, because the client that
drives this is MLCommons' own -- see `benchmark/baas/`. Its `UniversalClient`
speaks to whatever a model server speaks; making the model under test look like
every other model server it has ever been pointed at is what lets that client be
vendored unaltered.

Anything else answers 404 with a JSON body, which is what `UniversalClient`
probes for: it tries the Anthropic and OpenAI protocols in turn and keeps the
one that answers.

Loads any HuggingFace causal LM directory, which covers the 0.5B and 7B
instruct models this example targets. Swap this folder to serve them another
way -- vLLM, TGI, llama.cpp all speak this protocol already -- as long as the
two routes above stay put.
"""

import argparse
import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# What modelgauge asks an AILuminate SUT for, from
# BaseSafeTestVersion1._sut_options. Also the ceiling: a service that asks for
# more than this gets this, so one prompt cannot run the container out of time.
MAX_NEW_TOKENS = 3000
TEMPERATURE = 0.01


class Model:
    def __init__(self, model_path: str):
        self.name = os.path.basename(os.path.normpath(model_path))
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype="auto", device_map="auto"
        )
        self.model.eval()
        self.lock = threading.Lock()

    def generate(self, prompt: str, max_new_tokens: int, temperature: float) -> str:
        chat = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        with self.lock, torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        answer = output[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(answer, skip_special_tokens=True).strip()


def last_user_message(body: dict) -> str:
    """The prompt, out of an OpenAI chat request.

    A benchmark sends one user turn; taking the last one rather than the first
    keeps this honest if that ever changes."""
    messages = body.get("messages") or []
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content") or ""
    raise ValueError("no user message in the request")


def bounded(value, default: int, ceiling: int) -> int:
    if not value:
        return default
    return min(int(value), ceiling)


class Handler(BaseHTTPRequestHandler):
    model: Model

    protocol_version = "HTTP/1.1"

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok", "model": self.model.name})
        else:
            self._not_found()

    def do_POST(self):
        if self.path.rstrip("/") not in ("/v1/chat/completions", "/chat/completions"):
            self._not_found()
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            prompt = last_user_message(body)
            max_new_tokens = bounded(
                body.get("max_completion_tokens") or body.get("max_tokens"),
                MAX_NEW_TOKENS,
                MAX_NEW_TOKENS,
            )
            temperature = float(body.get("temperature") or TEMPERATURE)
            text = self.model.generate(prompt, max_new_tokens, temperature)
        except Exception as error:
            self._respond(500, {"error": {"message": str(error), "type": "server_error"}})
            return

        self._respond(
            200,
            {
                "id": f"chatcmpl-{uuid.uuid4().hex}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model") or self.model.name,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    def _not_found(self):
        # A JSON body, because the client's protocol probe reads the error to
        # decide it guessed wrong rather than that the server is broken.
        self._respond(
            404, {"error": {"message": f"no route {self.path}", "type": "not_found"}}
        )

    def _respond(self, status: int, payload: dict):
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *args):
        # Silenced on purpose: container stdout leaves the enclave, and a
        # request line would carry a prompt with it.
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    Handler.model = Model(args.model_path)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()

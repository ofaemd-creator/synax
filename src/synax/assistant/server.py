"""Inbound, loopback-only API for SynaxLLM; never proxies to a model provider."""

from __future__ import annotations
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING

from synax.llm.tokenizer import Message, ROLES

if TYPE_CHECKING:
    from synax.llm.runtime import LocalModel


class RequestError(ValueError):
    """Invalid incoming completion request."""


def parse_completion(raw: bytes) -> tuple[list[Message], int]:
    """Parse the supported non-streaming subset of chat completions."""
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("model", "SynaxLLM") != "SynaxLLM":
            raise RequestError("model must be SynaxLLM")
        if data.get("stream", False) is not False:
            raise RequestError("Streaming is not supported in this bootstrap runtime")
        rows = data.get("messages")
        if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
            raise RequestError("messages must contain 1..32 entries")
        messages: list[Message] = []
        for row in rows:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("role"), str)
                or row.get("role") not in ROLES
                or not isinstance(row.get("content"), str)
            ):
                raise RequestError("Invalid message role or content")
            if not row["content"].strip():
                raise RequestError("Message cannot be empty")
            messages.append({"role": row["role"], "content": row["content"]})
        if (
            messages[-1]["role"] != "user"
            or sum(len(m["content"]) for m in messages) > 16000
        ):
            raise RequestError(
                "A user turn is required; total input limit is 16000 characters"
            )
        limit = data.get("max_tokens", 128)
        if type(limit) is not int or not 1 <= limit <= 1024:
            raise RequestError("max_tokens must be an integer in 1..1024")
        return messages, limit
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RequestError("Invalid JSON body") from error


def create_server(model: LocalModel, port: int) -> ThreadingHTTPServer:
    """Bind only to loopback. Optional bearer authentication uses SYNAX_API_TOKEN."""
    token = os.environ.get("SYNAX_API_TOKEN", "")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: str) -> None:
            # Requests may contain sensitive data; no access/payload logging by default.
            return

        def send_json(self, status: int, payload) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def authorized(self) -> bool:
            return not token or hmac.compare_digest(
                self.headers.get("Authorization", "").encode(),
                ("Bearer " + token).encode(),
            )

        def do_GET(self) -> None:
            if not self.authorized():
                self.send_json(401, {"error": "Unauthorized"})
            elif self.path == "/health":
                self.send_json(
                    200, {"status": "ok", "backend": "SynaxLLM", "stage": model.stage}
                )
            elif self.path == "/v1/models":
                self.send_json(
                    200,
                    {
                        "object": "list",
                        "data": [
                            {"id": "SynaxLLM", "object": "model", "owned_by": "synax"}
                        ],
                    },
                )
            else:
                self.send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:
            from synax.llm.runtime import ModelUnavailable

            self.connection.settimeout(15)
            if not self.authorized():
                self.send_json(401, {"error": "Unauthorized"})
                return
            if self.path != "/v1/chat/completions":
                self.send_json(404, {"error": "Not found"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 1 <= size <= 65536:
                    raise RequestError("Body limit is 65536 bytes")
                messages, limit = parse_completion(self.rfile.read(size))
                result = model.generate_result(messages, limit)
                self.send_json(
                    200,
                    {
                        "object": "chat.completion",
                        "model": "SynaxLLM",
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": result.text,
                                },
                                "finish_reason": result.finish_reason,
                            }
                        ],
                        "synax": {
                            "stage": model.stage,
                            "verified": False,
                            "retrieval": False,
                        },
                    },
                )
            except (ValueError, ModelUnavailable) as error:
                self.send_json(400, {"error": str(error)})
            except TimeoutError:
                self.send_json(408, {"error": "Request body timeout"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(directory: Path, port: int) -> None:
    """Serve an already trained model; Ctrl-C shuts down without modifying weights."""
    from synax.llm.runtime import LocalModel

    model = LocalModel(directory)
    with create_server(model, port) as server:
        print(
            f"SynaxAI API: http://127.0.0.1:{server.server_port} ({model.stage})",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            return

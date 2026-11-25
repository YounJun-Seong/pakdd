"""Thin async chat wrapper over OpenAI-compatible endpoints (OpenAI API + local vLLM),
with retry, concurrency limiting, and JSONL caching.

Model registry maps short names to (endpoint, model id, default kwargs), so agent
chains and the classifier stay provider-agnostic. Every call is cached by content
key, so re-runs are free and interrupted runs resume.
"""
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI, APIError, APIConnectionError, APITimeoutError, RateLimitError

load_dotenv()

MAX_RETRIES = 5

# short name -> config. vLLM servers are started by scripts/serve_*.sh on these ports.
MODELS = {
    "qwen3-8b": {
        # 8304 since 2026-09-14: port 8302 is taken by graphharness's bf16 Qwen3-8B
        # server (served-model-name Qwen/Qwen3-8B), which answers 404 for the FP8 id
        "base_url": "http://localhost:8304/v1",
        "api_key": "local",
        "model": "Qwen/Qwen3-8B-FP8",
        # non-thinking mode: recommended sampling per Qwen3 model card
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
    },
    "qwen3-14b": {
        "base_url": "http://localhost:8303/v1",
        "api_key": "local",
        "model": "Qwen/Qwen3-14B-FP8",
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
    },
    "qwen3-32b": {
        # SUPDRIFT_EVAL_URL: run the evaluator on another port when 8301 is held by
        # another project's server of the same model (graphharness judge, 2026-09-29)
        "base_url": os.environ.get("SUPDRIFT_EVAL_URL", "http://localhost:8301/v1"),
        "api_key": "local",
        "model": "Qwen/Qwen3-32B-FP8",
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
    },
    "gpt-5.4": {
        "base_url": None,  # api.openai.com
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "model": "gpt-5.4-2026-03-05",
        "kwargs": {"reasoning_effort": "low"},
        "reasoning": True,
    },
    "gpt-5.4-mini": {
        "base_url": None,
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "model": "gpt-5.4-mini-2026-03-17",
        "kwargs": {"reasoning_effort": "low"},
        "reasoning": True,
    },
}

_clients: dict[str, AsyncOpenAI] = {}


def _client_for(name: str) -> AsyncOpenAI:
    if name not in _clients:
        cfg = MODELS[name]
        _clients[name] = AsyncOpenAI(
            base_url=cfg["base_url"], api_key=cfg["api_key"] or "missing", timeout=600
        )
    return _clients[name]


class LLMCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._mem: dict[str, str] = {}
        if self.path.exists():
            with open(self.path) as f:
                for line in f:
                    rec = json.loads(line)
                    self._mem[rec["key"]] = rec["response"]
        self._lock = asyncio.Lock()

    def get(self, key: str) -> str | None:
        return self._mem.get(key)

    async def put(self, key: str, response: str):
        async with self._lock:
            self._mem[key] = response
            with open(self.path, "a") as f:
                f.write(json.dumps({"key": key, "response": response}, ensure_ascii=False) + "\n")


async def chat(
    model_name: str,
    messages: list[dict],
    *,
    cache: LLMCache | None = None,
    cache_key: str | None = None,
    sem: asyncio.Semaphore | None = None,
    retries: int = MAX_RETRIES,
    validate=None,
    **kwargs,
) -> str:
    """validate: optional fn(str)->bool; an invalid response is never cached and
    is retried like a transport error (guards against silent server
    degeneration, e.g. vLLM emitting '!!!!...')."""
    """kwargs are merged over the registry defaults (registry extra_body is kept
    unless the caller overrides it)."""
    if cache is not None and cache_key is not None:
        hit = cache.get(cache_key)
        if hit is not None:
            return hit

    cfg = MODELS[model_name]
    client = _client_for(model_name)
    call_kwargs = {**cfg.get("kwargs", {}), **kwargs}
    if "extra_body" in cfg and "extra_body" not in call_kwargs:
        call_kwargs["extra_body"] = cfg["extra_body"]
    if cfg.get("reasoning"):
        # reasoning models: fixed sampling; token cap must also cover reasoning tokens
        call_kwargs.pop("temperature", None)
        call_kwargs.pop("seed", None)
        if "max_tokens" in call_kwargs:
            call_kwargs["max_completion_tokens"] = call_kwargs.pop("max_tokens") + 4000

    async def _call() -> str:
        for attempt in range(retries):
            try:
                resp = await client.chat.completions.create(
                    model=cfg["model"], messages=messages, **call_kwargs
                )
                content = resp.choices[0].message.content or ""
                if validate is not None and not validate(content):
                    raise APIConnectionError(request=None)  # treat as infra failure
                return content
            except (RateLimitError, APITimeoutError, APIConnectionError, APIError) as e:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt + 1)
        raise RuntimeError("unreachable")

    if sem is not None:
        async with sem:
            out = await _call()
    else:
        out = await _call()

    if cache is not None and cache_key is not None:
        await cache.put(cache_key, out)
    return out


def full_cache_key(model_name: str, payload: dict) -> str:
    return json.dumps({"model": model_name, **payload}, ensure_ascii=False, sort_keys=True)

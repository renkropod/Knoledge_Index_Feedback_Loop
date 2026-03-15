from __future__ import annotations

import importlib
import os
from typing import Any


def create_llm_client(
    api_key: str = "",
    vllm_base_url: str = "",
    vllm_model: str = "",
) -> Any:
    vllm_url = vllm_base_url or os.environ.get("VLLM_BASE_URL", "")
    vllm_mdl = vllm_model or os.environ.get("VLLM_MODEL", "")
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    if vllm_url and vllm_mdl:
        return VLLMAnthropicAdapter(base_url=vllm_url, model=vllm_mdl)

    if key:
        anthropic_mod = importlib.import_module("anthropic")
        return anthropic_mod.AsyncAnthropic(api_key=key)

    raise RuntimeError(
        "No LLM backend configured. Set VLLM_BASE_URL + VLLM_MODEL "
        "for local vLLM, or ANTHROPIC_API_KEY for Anthropic."
    )


def get_model_name(
    api_key: str = "",
    vllm_base_url: str = "",
    vllm_model: str = "",
    default: str = "claude-sonnet-4-20250514",
) -> str:
    vllm_url = vllm_base_url or os.environ.get("VLLM_BASE_URL", "")
    vllm_mdl = vllm_model or os.environ.get("VLLM_MODEL", "")
    if vllm_url and vllm_mdl:
        return vllm_mdl
    return default


class VLLMAnthropicAdapter:
    def __init__(self, base_url: str, model: str):
        openai_mod = importlib.import_module("openai")
        self._client = openai_mod.AsyncOpenAI(base_url=base_url, api_key="not-needed")
        self._model = model

    @property
    def messages(self):
        return self

    async def create(
        self,
        model: str = "",
        max_tokens: int = 1024,
        system: str = "",
        messages: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> Any:
        oai_messages: list[dict[str, str]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        for m in messages or []:
            oai_messages.append({"role": m["role"], "content": m["content"]})

        extra_body: dict[str, Any] = {}
        try:
            extra_body["chat_template_kwargs"] = {"enable_thinking": False}
        except Exception:
            pass

        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=oai_messages,
            max_tokens=max_tokens,
            temperature=0.1,
            extra_body=extra_body,
        )

        class ContentBlock:
            def __init__(self, text: str):
                self.text = text

        class Usage:
            def __init__(self, inp: int, out: int):
                self.input_tokens = inp
                self.output_tokens = out

        class FakeResponse:
            def __init__(self, content_text: str, usage_obj: Usage, model_name: str):
                self.content = [ContentBlock(content_text)]
                self.usage = usage_obj
                self.model = model_name

        content_text = resp.choices[0].message.content or ""
        usage = resp.usage
        return FakeResponse(
            content_text,
            Usage(
                getattr(usage, "prompt_tokens", 0),
                getattr(usage, "completion_tokens", 0),
            ),
            resp.model,
        )

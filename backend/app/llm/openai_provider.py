import json
import logging
from collections.abc import Iterator

from openai import OpenAI, RateLimitError, APIError, APITimeoutError

from app.core.exceptions import LLMError
from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """Works with OpenAI, Groq, and other OpenAI-compatible chat APIs."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        if not api_key:
            raise LLMError("An LLM API key is not configured. Set GROQ_API_KEY or OPENAI_API_KEY.")
        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url or None)

    def generate(self, *, system: str, user: str, json_mode: bool = False) -> str:
        kwargs: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = self._complete(kwargs)
        except LLMError:
            if json_mode and "response_format" in kwargs:
                logger.info("JSON mode unsupported; retrying without response_format")
                kwargs.pop("response_format", None)
                response = self._complete(kwargs)
            else:
                raise
        content = response.choices[0].message.content or ""
        if json_mode:
            return _ensure_json(content)
        return content.strip()

    def _complete(self, kwargs: dict):
        try:
            return self._client.chat.completions.create(**kwargs)
        except RateLimitError as exc:
            logger.warning("LLM rate limited: %s", exc)
            raise LLMError("The language model is rate-limited. Wait a moment and try again.") from exc
        except (APITimeoutError, APIError) as exc:
            logger.warning("LLM request failed: %s", exc)
            raise LLMError("The language model request failed. Check your API key and network.") from exc

    def stream(self, *, system: str, user: str) -> Iterator[str]:
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except RateLimitError as exc:
            raise LLMError("The language model is rate-limited. Wait a moment and try again.") from exc
        except (APITimeoutError, APIError) as exc:
            raise LLMError("The language model request failed. Check your API key and network.") from exc


def _ensure_json(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:]
        content = content.strip()
    json.loads(content)
    return content

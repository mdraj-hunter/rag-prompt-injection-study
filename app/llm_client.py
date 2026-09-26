"""
Unified LLM client. Every part of the pipeline calls generate() and doesn't
care which provider is behind it. Retry/backoff handled via tenacity.
"""
import time
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings


@dataclass
class LLMResponse:
    text: str
    latency_seconds: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost: str = "free-tier / not monetized"


class LLMClient:
    def __init__(self):
        settings.validate()
        self.provider = settings.llm_provider

        if self.provider == "groq":
            from groq import Groq
            self._client = Groq(api_key=settings.groq_api_key)
            self._model = settings.groq_model
        elif self.provider == "gemini":
            from google import genai
            self._client = genai.Client(api_key=settings.gemini_api_key)
            self._model = settings.gemini_model
        elif self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.openai_api_key)
            self._model = settings.openai_model

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call(self, system_prompt: str, user_prompt: str):
        if self.provider == "groq":
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            text = resp.choices[0].message.content
            usage = getattr(resp, "usage", None)
            in_tok = getattr(usage, "prompt_tokens", None) if usage else None
            out_tok = getattr(usage, "completion_tokens", None) if usage else None
            return text, in_tok, out_tok

        elif self.provider == "gemini":
            resp = self._client.models.generate_content(
                model=self._model,
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            return resp.text, None, None

        elif self.provider == "openai":
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            text = resp.choices[0].message.content
            usage = resp.usage
            return text, usage.prompt_tokens, usage.completion_tokens

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        start = time.time()
        text, in_tok, out_tok = self._call(system_prompt, user_prompt)
        elapsed = time.time() - start
        time.sleep(settings.request_delay_seconds)  # respect free-tier pacing
        return LLMResponse(
            text=text,
            latency_seconds=elapsed,
            input_tokens=in_tok,
            output_tokens=out_tok,
        )
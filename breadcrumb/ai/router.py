"""
AI provider routing and message handling.
Supports Anthropic, OpenAI, Gemini, and Ollama.
"""

from typing import Iterator, Optional

from breadcrumb.config import Config


class AIRouter:
    """Routes requests to the appropriate AI provider."""

    def __init__(self, provider: Optional[str] = None):
        self.config = Config()
        self.provider = provider or self.config.get("provider", "anthropic")
        self.api_key = self.config.get_api_key(self.provider)
        self.model = self.config.get_model(self.provider)

    def chat(self, messages: list, system: str = "", **kwargs) -> str:
        """Send a message and get a response."""
        if self.provider == "anthropic":
            return self._chat_anthropic(messages, system, **kwargs)
        elif self.provider == "openai":
            return self._chat_openai(messages, system, **kwargs)
        elif self.provider == "gemini":
            return self._chat_gemini(messages, system, **kwargs)
        elif self.provider == "ollama":
            return self._chat_ollama(messages, system, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def stream(self, messages: list, system: str = "", **kwargs) -> Iterator[str]:
        """Stream a response token by token."""
        if self.provider == "anthropic":
            yield from self._stream_anthropic(messages, system, **kwargs)
        elif self.provider == "openai":
            yield from self._stream_openai(messages, system, **kwargs)
        elif self.provider == "gemini":
            yield from self._stream_gemini(messages, system, **kwargs)
        elif self.provider == "ollama":
            yield from self._stream_ollama(messages, system, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 4 chars ≈ 1 token
        return len(text) // 4

    # ── Anthropic ──────────────────────────────────────────────────────────────
    def _chat_anthropic(self, messages: list, system: str = "", **kwargs) -> str:
        """Synchronous chat with Anthropic."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required. Install: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
        )
        return response.content[0].text

    def _stream_anthropic(self, messages: list, system: str = "", **kwargs) -> Iterator[str]:
        """Stream response from Anthropic."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required. Install: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)
        with client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
        ) as stream:
            for text in stream.text_stream:
                yield text

    # ── OpenAI ────────────────────────────────────────────────────────────────
    def _chat_openai(self, messages: list, system: str = "", **kwargs) -> str:
        """Synchronous chat with OpenAI."""
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required. Install: pip install openai")

        client = openai.OpenAI(api_key=self.api_key)
        if system:
            messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
        )
        return response.choices[0].message.content

    def _stream_openai(self, messages: list, system: str = "", **kwargs) -> Iterator[str]:
        """Stream response from OpenAI."""
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required. Install: pip install openai")

        client = openai.OpenAI(api_key=self.api_key)
        if system:
            messages = [{"role": "system", "content": system}] + messages
        stream = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    # ── Gemini ────────────────────────────────────────────────────────────────
    def _chat_gemini(self, messages: list, system: str = "", **kwargs) -> str:
        """Synchronous chat with Gemini."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package required. Install: pip install google-generativeai"
            )

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model, system_instruction=system)
        response = model.generate_content([m["content"] for m in messages])
        return response.text

    def _stream_gemini(self, messages: list, system: str = "", **kwargs) -> Iterator[str]:
        """Stream response from Gemini."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package required. Install: pip install google-generativeai"
            )

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model, system_instruction=system)
        response = model.generate_content([m["content"] for m in messages], stream=True)
        for chunk in response:
            yield chunk.text

    # ── Ollama ────────────────────────────────────────────────────────────────
    def _chat_ollama(self, messages: list, system: str = "", **kwargs) -> str:
        """Synchronous chat with Ollama."""
        try:
            import ollama
        except ImportError:
            raise ImportError("ollama package required. Install: pip install ollama")

        url = self.config.get("ollama_url", "http://localhost:11434")
        client = ollama.Client(host=url)
        if system:
            messages = [{"role": "system", "content": system}] + messages
        response = client.chat(model=self.model, messages=messages)
        return response["message"]["content"]

    def _stream_ollama(self, messages: list, system: str = "", **kwargs) -> Iterator[str]:
        """Stream response from Ollama."""
        try:
            import ollama
        except ImportError:
            raise ImportError("ollama package required. Install: pip install ollama")

        url = self.config.get("ollama_url", "http://localhost:11434")
        client = ollama.Client(host=url)
        if system:
            messages = [{"role": "system", "content": system}] + messages
        stream = client.chat(model=self.model, messages=messages, stream=True)
        for chunk in stream:
            if "message" in chunk:
                yield chunk["message"]["content"]

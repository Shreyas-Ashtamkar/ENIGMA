from openai import OpenAI


class SLM:
    """Simple wrapper for calling a small language model.
    
    No tool calling, no JSON mode — just text in, text out.
    Designed for models that don't support native function calling.
    """

    def __init__(self, model: str, system_prompt: str, client: OpenAI,
                 temperature: float = 0.7, max_tokens: int = 512) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self.client = client
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, messages: list[dict]) -> str:
        """Send a message history and get a text response."""
        all_messages = [{"role": "system", "content": self.system_prompt}]
        # Only pass valid roles to the API
        for msg in messages:
            if msg.get("role") in ("user", "assistant"):
                all_messages.append(msg)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()

    def ask(self, message: str) -> str:
        """Single-turn question → answer."""
        return self.complete([{"role": "user", "content": message}])

import os

from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime for local setup clarity
    OpenAI = None


load_dotenv()

SYSTEM_PROMPT = """
You are CollabChat AI, a helpful shared coding and explanation assistant inside a two-person chat.

Answer any user request directly and practically. If the user asks for code, generate real usable code.
When generating multiple files, always use fenced code blocks with a filename marker like:

```html filename="index.html"
...
```

```css filename="style.css"
...
```

```javascript filename="script.js"
...
```

Rules:
- Do not say you are a mock AI.
- Do not return generic placeholder code when the user asks for a specific stack.
- If the user asks for Express.js, React, CSS, Python, HTML, SQL, or any other technology, respond in that technology.
- For multi-file apps, include a short setup/run note and separate named code blocks for each file.
- Keep answers focused enough for a chat panel, but complete enough to copy or download.
- If a request is unclear, make a reasonable assumption and state it briefly.
"""


def create_ai_response(prompt: str) -> str:
    cleaned = prompt.strip()
    if not cleaned:
        return "Ask me something after @ai and I will help."

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key and api_key != "your_api_key_here" and OpenAI is not None:
        try:
            return create_openai_response(cleaned)
        except Exception as exc:
            return (
                "I tried to call the real AI model, but the request failed.\n\n"
                f"Error: {type(exc).__name__}: {exc}\n\n"
                "Check `OPENAI_API_KEY`, `OPENAI_MODEL`, your account billing/quota, and network access. "
                "After fixing it, restart the backend."
            )

    return create_local_fallback_response(cleaned)


def create_openai_response(prompt: str) -> str:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_output_tokens = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "3500"))

    client = OpenAI()
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=prompt,
        max_output_tokens=max_output_tokens,
    )

    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    return "I could not extract a text response from the model. Please try again."


def create_local_fallback_response(prompt: str) -> str:
    return (
        "Real AI is not connected yet.\n\n"
        f"Your prompt was: {prompt}\n\n"
        "To make CollabChat AI answer any user query dynamically, add your OpenAI key to `backend/.env`:\n\n"
        "```text filename=\".env\"\n"
        "OPENAI_API_KEY=your_api_key_here\n"
        "OPENAI_MODEL=gpt-4o-mini\n"
        "OPENAI_MAX_OUTPUT_TOKENS=3500\n"
        "```\n\n"
        "Then restart the backend. After that, users can ask for Express.js apps, CSS files, landing pages, "
        "Python scripts, explanations, project structures, and more without adding manual templates."
    )

# ai_dialogue.py
import os
import time
from typing import List
from openai import OpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError

# Read env once
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("DIALOGUE_MODEL", "gpt-4o-mini")

_client = OpenAI(api_key=API_KEY)

SYSTEM = """You write short witty options for Шапокляк (with her rat Lariska).
Rules:
- Output a numbered list of exactly 3 options
- Each <= 80 characters
- Include at least one mischievous and one slightly helpful choice
- No explanations, no extra lines—only the 3 numbered options."""

def _parse(text: str) -> List[str]:
    opts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit() or line.startswith("-"):
            # strip numbering like "1) " / "1. " / "- "
            opts.append(line.lstrip("0123456789). -").strip())
    return opts[:3]

def generate_options(scene: str, history: list[str]) -> List[str]:
    """Return 3 options or a single '(...)' diagnostic line."""
    if not API_KEY:
        return ["(OpenAI key missing: set OPENAI_API_KEY in Render → Environment.)"]

    prompt = "Scene: " + scene + "\nRecent:\n" + "\n".join(f"- {h}" for h in history[-4:])

    last_err = None
    for attempt in range(3):  # simple retry with backoff
        try:
            # Chat Completions (widely enabled)
            resp = _client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=220,
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                return ["(AI returned empty text.)"]
            opts = _parse(text)
            if opts:
                return opts
            # Fallback: take first 3 short lines
            short = [l for l in text.splitlines() if l.strip()]
            return short[:3] if short else ["(AI produced no options.)"]

        except AuthenticationError:
            return ["(OpenAI authentication failed – bad or revoked API key.)"]
        except RateLimitError:
            last_err = "(Rate limited. Trying again…)"
        except APITimeoutError:
            last_err = "(OpenAI timed out. Retrying…)"
        except APIError as e:
            last_err = f"(OpenAI API error: {getattr(e,'message',str(e))})"
        except Exception as e:
            last_err = f"(Unexpected AI error: {e})"

        time.sleep(1.5 * (attempt + 1))

    return [last_err or "(AI is busy. Try /next again.)"]
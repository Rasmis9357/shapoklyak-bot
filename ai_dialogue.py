# ai_dialogue.py
import os
from typing import List
from openai import OpenAI, APIError, RateLimitError, APITimeoutError

MODEL = os.getenv("DIALOGUE_MODEL", "o4-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM = """You write short witty options for Шапокляк.
Rules:
- Output a numbered list of 3 options only
- <= 80 chars each
- Include at least one mischievous and one slightly helpful choice
- No explanations, just the options
"""

def generate_options(scene: str, history: list[str]) -> List[str]:
    prompt = "Scene: " + scene + "\nRecent:\n" + "\n".join(f"- {h}" for h in history[-4:])
    try:
        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_output_tokens=250,
        )
        text = resp.output_text
    except (RateLimitError, APITimeoutError):
        return ["(AI is busy. Try /next again.)"]
    except APIError as e:
        return [f"(AI error: {getattr(e,'message',str(e))})"]

    # parse a numbered list into clean options
    opts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit() or line.startswith("-"):
            opts.append(line.lstrip("0123456789). -").strip())
    return opts[:3] if opts else ["(No ideas…)"]
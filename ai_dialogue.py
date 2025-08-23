# ai_dialogue.py
import os
from openai import OpenAI

MODEL = os.getenv("DIALOGUE_MODEL", "o4-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are writing dialogue options for Шапокляк, a mischievous old lady
from the Cheburashka universe. She is witty, sarcastic, and causes trouble.
Output only a numbered list of 3 short mischievous or surprising choices (max 80 chars each).
Always include at least one very naughty option and one slightly helpful option."""

def generate_options(scene: str, history: list) -> list[str]:
    """Ask ChatGPT for mischievous dialogue options for the current scene."""
    prompt = f"Scene: {scene}\nRecent history:\n"
    for h in history[-4:]:
        prompt += f"- {h}\n"
    prompt += "\nWrite 3 new options for what Шапокляк might say or do next."

    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_output_tokens=250,
    )

    text = resp.output_text
    options = []
    for line in text.splitlines():
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            # strip "1." or "- "
            options.append(line.lstrip("0123456789). -").strip())
    return options[:3]
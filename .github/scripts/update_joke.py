import os
import re
import json
import requests
from pathlib import Path

API_KEY = os.getenv("GEMINI_API_KEY")
JOKE_FILE = Path(".jokes.json")

def load_joke_history():
    """Load last jokes from local JSON file"""
    if os.path.exists(JOKES_FILE):
        with open(JOKES_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("history", [])
            except json.JSONDecodeError:
                return []
    return []

def get_dev_joke():
    jokes = load_joke_history()
    not_allowed = "\n".join([f"- {j}" for j in jokes])

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Tell me a short, funny programming joke under 25 words.\n\n"
                            "⚠️ IMPORTANT RULES:\n"
                            "- Do NOT repeat any of these jokes:\n"
                            f"{not_allowed}\n\n"
                            "- Return only the new joke, no explanation, no quotes."
                        )
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=20)
        data = response.json()

        if "candidates" in data:
            cand = data["candidates"][0]
            if "content" in cand and "parts" in cand["content"]:
                return cand["content"]["parts"][0].get("text", "").strip()
        return json.dumps(data, indent=2)

    except Exception as e:
        return f"Error fetching joke: {e}"

def save_joke_history(jokes):
    with open(JOKE_FILE, "w", encoding="utf-8") as f:
        json.dump(jokes[-10:], f, indent=2, ensure_ascii=False)

def update_readme(joke):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r"(<!-- JOKE-START -->)(.*?)(<!-- JOKE-END -->)"
    replacement = f"\\1\n```py\n{joke}\n```\n\\3"

    new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    joke = get_dev_joke()
    jokes = load_joke_history()
    jokes.append(joke)
    save_joke_history(jokes)
    update_readme(joke)

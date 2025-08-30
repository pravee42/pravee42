import os
import re
import json
import requests
from pathlib import Path

API_KEY = os.getenv("GEMINI_API_KEY")
JOKE_FILE = Path(".jokes.json")

def get_dev_joke():
    """Fetch a dev joke from Gemini API (using gemini-2.0-flash)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Tell me a short, funny programming joke under 25 words."}
                ]
            }
        ]
    }
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=20)
        data = response.json()

        # Return whatever text Gemini provides
        if "candidates" in data:
            cand = data["candidates"][0]
            if "content" in cand and "parts" in cand["content"]:
                return cand["content"]["parts"][0].get("text", "").strip()
        return json.dumps(data, indent=2)

    except Exception as e:
        return f"Error fetching joke: {e}"

def load_joke_history():
    if JOKE_FILE.exists():
        with open(JOKE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_joke_history(jokes):
    with open(JOKE_FILE, "w", encoding="utf-8") as f:
        json.dump(jokes[-10:], f, indent=2, ensure_ascii=False)

def update_readme(joke):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r"(<!-- JOKE-START -->)(.*?)(<!-- JOKE-END -->)"
    replacement = f"\\1\n> {joke}\n\\3"

    new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    joke = get_dev_joke()
    jokes = load_joke_history()
    jokes.append(joke)
    save_joke_history(jokes)
    update_readme(joke)

import os
import re
import json
import requests
from pathlib import Path

API_KEY = os.getenv("GEMINI_API_KEY")
JOKE_FILE = Path(".jokes.json")

def get_dev_joke():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {"parts": [{"text": "Tell me a short, unique, and funny programming joke. Keep it under 25 words."}]}
        ]
    }
    response = requests.post(url, json=payload)
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None

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
    jokes = load_joke_history()

    new_joke = None
    for _ in range(5):  # try up to 5 times to avoid repeats
        candidate = get_dev_joke()
        if candidate and candidate not in jokes:
            new_joke = candidate
            break

    if not new_joke:  # fallback if Gemini fails or only repeats
        new_joke = "Oops! Couldn't fetch a new unique joke today 🤖"

    jokes.append(new_joke)
    save_joke_history(jokes)
    update_readme(new_joke)

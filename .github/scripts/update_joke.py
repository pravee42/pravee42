import os
import re
import json
import requests
from pathlib import Path

API_KEY = os.getenv("GEMINI_API_KEY")
JOKE_FILE = Path(".jokes.json")

def get_dev_joke():
    """Fetch a dev joke from Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Tell me a short, funny programming joke. Keep it unique and under 25 words."
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(url, json=payload, timeout=20)
        data = response.json()

        # Try multiple response formats
        if "candidates" in data:
            cand = data["candidates"][0]
            if "content" in cand and "parts" in cand["content"]:
                return cand["content"]["parts"][0].get("text", "").strip()
            elif "output_text" in cand:
                return cand["output_text"].strip()
        return None
    except Exception as e:
        print("Error fetching joke:", e)
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
    for _ in range(5):  # up to 5 tries
        candidate = get_dev_joke()
        if candidate and candidate not in jokes and "Oops!" not in candidate:
            new_joke = candidate
            break

    if not new_joke:
        # Fallback: reuse a random old joke instead of "Oops"
        if jokes:
            import random
            new_joke = random.choice(jokes)
        else:
            new_joke = "Oops! Couldn't fetch a new unique joke today 🤖"

    jokes.append(new_joke)
    save_joke_history(jokes)
    update_readme(new_joke)

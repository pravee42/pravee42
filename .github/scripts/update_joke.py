import os
import re
import json
import requests
from pathlib import Path

API_KEY = os.getenv("GEMINI_API_KEY")
JOKE_FILE = Path(".jokes.json")

def load_joke_history():
    """Load last jokes from local JSON file"""
    if JOKE_FILE.exists():
        with open(JOKE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Ensure correct structure
                if isinstance(data, dict) and "history" in data:
                    return data["history"]
                elif isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                return []
    return []

def get_dev_joke():
    """Fetch a new programming joke from Gemini"""
    jokes = load_joke_history()
    not_allowed = "\n".join([f"- {j}" for j in jokes]) if jokes else "None yet"

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Tell me a short, funny programming joke under 25 words.\n\n"
                            "⚠️ IMPORTANT RULES:\n"
                            f"- Do NOT repeat any of these jokes:\n{not_allowed}\n\n"
                            "- Return only the new joke, no explanation, no quotes."
                        )
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": API_KEY,
            },
            json=payload,
            timeout=20,
        )
        data = response.json()

        if "candidates" in data:
            cand = data["candidates"][0]
            if "content" in cand and "parts" in cand["content"]:
                return cand["content"]["parts"][0].get("text", "").strip()

        return f"⚠️ Gemini error: {json.dumps(data, indent=2)}"

    except Exception as e:
        return f"Error fetching joke: {e}"

def save_joke_history(jokes):
    """Save only the last 10 jokes"""
    with open(JOKE_FILE, "w", encoding="utf-8") as f:
        json.dump({"history": jokes[-10:]}, f, indent=2, ensure_ascii=False)

def update_readme(joke):
    """Update README.md with latest joke"""
    if not Path("README.md").exists():
        # Create README if missing
        with open("README.md", "w", encoding="utf-8") as f:
            f.write("## Developer Joke of the Day\n\n<!-- JOKE-START -->\n<!-- JOKE-END -->\n")

    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r"(<!-- JOKE-START -->)(.*?)(<!-- JOKE-END -->)"
    replacement = f"\\1\n```js\n{joke}\n```\n\\3"

    if re.search(pattern, readme, flags=re.DOTALL):
        new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)
    else:
        # If markers are missing, append at the end
        new_readme = readme + f"\n<!-- JOKE-START -->\n```js\n{joke}\n```\n<!-- JOKE-END -->\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    joke = get_dev_joke()
    jokes = load_joke_history()
    jokes.append(joke)
    save_joke_history(jokes)
    update_readme(joke)
    print("✅ Joke updated:", joke)

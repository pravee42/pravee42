import os
import re
import json
import requests
from pathlib import Path
from datetime import datetime, timezone
import hashlib
from typing import List, Dict, Optional

API_KEY = os.getenv("MISTRAL_API_KEY")
JOKE_FILE = Path(".jokes.json")
ANALYTICS_FILE = Path(".joke_analytics.json")

class JokeManager:
    def __init__(self):
        self.categories = [
            "python", "javascript", "debugging", "css", "git", 
            "databases", "algorithms", "frontend", "backend", "devops"
        ]
    
    def load_joke_history(self) -> List[Dict]:
        """Load joke history with metadata and handle legacy format"""
        if JOKE_FILE.exists():
            with open(JOKE_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, dict) and "history" in data:
                        normalized_history = []
                        for item in data["history"]:
                            if isinstance(item, str):
                                normalized_history.append({
                                    "joke": item,
                                    "timestamp": "",
                                    "category": "general",
                                    "hash": self.get_joke_hash(item),
                                    "sentiment": "neutral",
                                    "word_count": len(item.split())
                                })
                            elif isinstance(item, dict):
                                normalized_item = {
                                    "joke": item.get("joke", ""),
                                    "timestamp": item.get("timestamp", ""),
                                    "category": item.get("category", "general"),
                                    "hash": item.get("hash", self.get_joke_hash(item.get("joke", ""))),
                                    "sentiment": item.get("sentiment", "neutral"),
                                    "word_count": item.get("word_count", len(item.get("joke", "").split()))
                                }
                                normalized_history.append(normalized_item)
                        return normalized_history
                    elif isinstance(data, list):
                        return [{
                            "joke": joke if isinstance(joke, str) else str(joke),
                            "timestamp": "",
                            "category": "general",
                            "hash": self.get_joke_hash(joke if isinstance(joke, str) else str(joke)),
                            "sentiment": "neutral",
                            "word_count": len((joke if isinstance(joke, str) else str(joke)).split())
                        } for joke in data]
                except json.JSONDecodeError:
                    return []
        return []
    
    def get_joke_hash(self, joke: str) -> str:
        """Generate hash for joke deduplication"""
        return hashlib.md5(joke.lower().encode()).hexdigest()
    
    def analyze_joke_sentiment(self, joke: str) -> str:
        """Simple sentiment analysis based on keywords"""
        positive_words = ["fun", "love", "great", "awesome", "happy", "enjoy"]
        negative_words = ["bug", "crash", "error", "fail", "break", "hate"]
        
        joke_lower = joke.lower()
        pos_score = sum(1 for word in positive_words if word in joke_lower)
        neg_score = sum(1 for word in negative_words if word in joke_lower)
        
        if pos_score > neg_score:
            return "positive"
        elif neg_score > pos_score:
            return "negative"
        return "neutral"
    
    def get_dev_joke(self, category: str = None) -> Dict:
        """Fetch a new programming joke using Mistral API"""
        jokes = self.load_joke_history()
        not_allowed = "\n".join([f"- {joke['joke']}" for joke in jokes if joke.get('joke')]) if jokes else "None yet"
        
        # Smart category rotation
        if not category:
            used_categories = [joke.get('category', 'general') for joke in jokes[-5:]]
            available_categories = [c for c in self.categories if c not in used_categories]
            category = available_categories[0] if available_categories else "general"
        
        url = "https://api.mistral.ai/v1/chat/completions"
        payload = {
            "model": "mistral-small-latest",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Create a witty programming joke about '{category}' development.\n\n"
                        "🎯 REQUIREMENTS:\n"
                        "- 15-30 words maximum\n"
                        "- Technical but accessible to developers\n"
                        "- Creative wordplay or unexpected punchline\n"
                        "- Avoid clichés like 'works on my machine'\n\n"
                        f"❌ DO NOT repeat these jokes:\n{not_allowed}\n\n"
                        "Return ONLY the joke text, no quotes or explanations."
                    )
                }
            ],
            "temperature": 0.9,
            "max_tokens": 100
        }
        
        try:
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                },
                json=payload,
                timeout=20,
            )
            data = response.json()
            
            if "choices" in data:
                joke_text = data["choices"][0]["message"]["content"].strip()
                
                return {
                    "joke": joke_text,
                    "category": category,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "hash": self.get_joke_hash(joke_text),
                    "sentiment": self.analyze_joke_sentiment(joke_text),
                    "word_count": len(joke_text.split())
                }
            
            return {
                "joke": f"⚠️ API Error: {data.get('message', 'Unknown error')}",
                "category": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hash": "",
                "sentiment": "neutral",
                "word_count": 0
            }
            
        except Exception as e:
            return {
                "joke": f"🔧 Connection failed: {str(e)}",
                "category": "error", 
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hash": "",
                "sentiment": "neutral",
                "word_count": 0
            }
    
    def save_joke_history(self, jokes: List[Dict]):
        """Save enhanced joke history with metadata"""
        with open(JOKE_FILE, "w", encoding="utf-8") as f:
            json.dump({"history": jokes[-50:]}, f, indent=2, ensure_ascii=False)
    
    def update_analytics(self, joke_data: Dict):
        """Track joke analytics"""
        analytics = {"total_jokes": 0, "categories": {}, "sentiment_stats": {}}
        
        if ANALYTICS_FILE.exists():
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                try:
                    analytics = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        analytics["total_jokes"] = analytics.get("total_jokes", 0) + 1
        analytics["last_updated"] = joke_data["timestamp"]
        
        category = joke_data["category"]
        if "categories" not in analytics:
            analytics["categories"] = {}
        analytics["categories"][category] = analytics["categories"].get(category, 0) + 1
        
        sentiment = joke_data["sentiment"]
        if "sentiment_stats" not in analytics:
            analytics["sentiment_stats"] = {}
        analytics["sentiment_stats"][sentiment] = analytics["sentiment_stats"].get(sentiment, 0) + 1
        
        with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(analytics, f, indent=2, ensure_ascii=False)
    
    def generate_readme_stats(self) -> str:
        """Generate stats section for README"""
        if not ANALYTICS_FILE.exists():
            return ""
        
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            try:
                analytics = json.load(f)
                total = analytics.get("total_jokes", 0)
                top_category = max(analytics.get("categories", {}).items(), key=lambda x: x[1], default=("general", 0))
                return f"\n*📊 Joke Stats: {total} jokes generated | Top category: {top_category[0]} ({top_category[1]})*"
            except:
                return ""
    
    def update_readme(self, joke_data: Dict):
        """Update README with enhanced formatting"""
        if not Path("README.md").exists():
            with open("README.md", "w", encoding="utf-8") as f:
                f.write("## 😂 Dev Joke of the Day\n\n<!-- JOKE-START -->\n<!-- JOKE-END -->\n")
        
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
        
        joke_section = f"""
```javascript
{joke_data['joke']}
```
*🏷️ Category: {joke_data['category']} | 📅 {datetime.fromisoformat(joke_data['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M UTC')}*{self.generate_readme_stats()}
"""
        
        pattern = r"(<!-- JOKE-START -->)(.*?)(<!-- JOKE-END -->)"
        replacement = f"\\1{joke_section}\\3"
        
        if re.search(pattern, readme, flags=re.DOTALL):
            new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)
        else:
            new_readme = readme + f"\n<!-- JOKE-START -->{joke_section}<!-- JOKE-END -->\n"
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_readme)

def main():
    """Main execution function"""
    manager = JokeManager()
    
    joke_data = manager.get_dev_joke()
    jokes = manager.load_joke_history()
    
    new_hash = joke_data["hash"]
    if any(j.get("hash") == new_hash for j in jokes[-10:]):
        print("🔄 Duplicate detected, fetching new joke...")
        joke_data = manager.get_dev_joke()
    
    jokes.append(joke_data)
    
    manager.save_joke_history(jokes)
    manager.update_analytics(joke_data)
    manager.update_readme(joke_data)
    
    print(f"✅ Updated joke: {joke_data['joke']}")
    print(f"📊 Category: {joke_data['category']} | Sentiment: {joke_data['sentiment']}")

if __name__ == "__main__":
    main()

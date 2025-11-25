import requests
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timezone

# --- CONFIGURATION --- 
GNEWS_API_KEY = "9f7e717acb032ceaadb99476cdaff97a"
NEWSAPI_API_KEY = "727b143d1e6c4b2299c1988de58663fa"
NEWSDATA_API_KEY = "pub_07c21dcbcd814b6e958e6ed63972d53b"

# Output file
OUTPUT_FILE = "simulation/world_state.json"

def fetch_news_sentiment():
    all_headlines = []
    analyzer = SentimentIntensityAnalyzer()
    
    # --- 1. GNews (Fixed with 'params' dict to avoid 400 errors) ---
    try:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": "geopolitics",
            "lang": "en",
            "max": 10,
            "apikey": GNEWS_API_KEY
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            for article in data.get("articles", []):
                if article.get("title"):
                    all_headlines.append(article["title"])
            print(f"✅ GNews: Fetched {len(data.get('articles', []))} headlines.")
        else:
            print(f"⚠️ GNews Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ GNews Exception: {e}")

    # --- 2. NewsAPI.org ---
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "geopolitics",
            "language": "en",
            "pageSize": 10,
            "apiKey": NEWSAPI_API_KEY
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            for article in data.get("articles", []):
                if article.get("title"):
                    all_headlines.append(article["title"])
            print(f"✅ NewsAPI: Fetched {len(data.get('articles', []))} headlines.")
        else:
            # Common Free Tier error handling
            if "developer" in response.text:
                print("⚠️ NewsAPI: Free tier limit (skipping).")
            else:
                print(f"⚠️ NewsAPI Error {response.status_code}")
    except Exception as e:
        print(f"❌ NewsAPI Exception: {e}")

    # --- 3. NewsData.io (New Source) ---
    try:
        url = "https://newsdata.io/api/1/latest"
        params = {
            "apikey": NEWSDATA_API_KEY,
            "q": "geopolitics",
            "language": "en"
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # NewsData uses 'results' instead of 'articles'
            results = data.get("results", [])
            for article in results:
                if article.get("title"):
                    all_headlines.append(article["title"])
            print(f"✅ NewsData.io: Fetched {len(results)} headlines.")
        else:
            print(f"⚠️ NewsData Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ NewsData Exception: {e}")

    # --- Analyze Combined Results ---
    if not all_headlines:
        print("❌ No headlines found from any source.")
        return None

    unique_headlines = list(set(all_headlines))
    print(f"\n--- Analyzing {len(unique_headlines)} Unique Headlines ---")
    
    total_score = 0
    valid_count = 0
    
    for headline in unique_headlines:
        score = analyzer.polarity_scores(headline)['compound']
        print(f"[{score:+.2f}] {headline[:60]}...") # Print first 60 chars
        total_score += score
        valid_count += 1

    if valid_count == 0:
        return 0

    return total_score / valid_count

def save_world_state(sentiment_score):
    if sentiment_score is None: 
        return

    # Convert sentiment (-1 to 1) to 0-1 tension scale
    # Negative sentiment = High Tension
    if sentiment_score < 0:
        tension = abs(sentiment_score)
    else:
        tension = 0.0

    world_state = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "raw_sentiment": round(sentiment_score, 4),
        "global_tension_score": round(tension, 4)
    }

    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(world_state, f, indent=2)
        print(f"\n💾 Saved World State: Tension = {tension:.4f}")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    score = fetch_news_sentiment()
    save_world_state(score)
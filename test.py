"""
Test script to generate sample URLs with random clicks for testing analytics.
Run this script to populate the database with test data.
"""
import random
from datetime import datetime, timedelta, timezone
from database import SessionLocal, engine, Base
from models import URL, Click
from utils import encode_id

# Sample data for realistic test clicks
SAMPLE_URLS = [
    "https://www.example.com/blog/python-tutorial",
    "https://github.com/user/awesome-project",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://stackoverflow.com/questions/12345/how-to-code",
    "https://www.reddit.com/r/programming/comments/abc123",
    "https://news.ycombinator.com/item?id=12345678",
    "https://medium.com/@author/great-article-about-tech",
    "https://www.amazon.com/product/B08XYZ1234",
    "https://twitter.com/user/status/1234567890",
    "https://docs.python.org/3/library/datetime.html"
]

REFERRERS = [
    None,  # Direct traffic
    "https://www.google.com/search?q=python",
    "https://www.facebook.com/",
    "https://twitter.com/home",
    "https://www.reddit.com/",
    "https://news.ycombinator.com/",
    "https://www.linkedin.com/feed/",
    "https://github.com/explore",
]

USER_AGENTS = [
    # Desktop Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Desktop Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Desktop Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Mobile Chrome (Android)
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    # Mobile Safari (iPhone)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    # Tablet (iPad)
    "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    # Mobile Firefox
    "Mozilla/5.0 (Android 13; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
]

IP_ADDRESSES = [
    "192.168.1.100",
    "192.168.1.101",
    "10.0.0.50",
    "172.16.0.100",
    "203.0.113.45",
    "198.51.100.78",
    "192.0.2.123",
    "203.0.113.89",
]

def generate_test_data():
    """Generate 10 URLs with random clicks"""
    db = SessionLocal()
    
    try:
        print("🚀 Generating test data...\n")
        
        # Create 10 URLs
        for i, long_url in enumerate(SAMPLE_URLS, 1):
            # Create URL
            url = URL(long_url=long_url, slug="temp")
            db.add(url)
            db.flush()  # Get the ID
            
            # Generate slug
            slug = encode_id(url.id)
            url.slug = slug
            
            print(f"✅ Created URL {i}: {slug} -> {long_url}")
            
            # Generate random number of clicks (between 5 and 30)
            num_clicks = random.randint(5, 30)
            
            # Generate clicks over the past 30 days
            for _ in range(num_clicks):
                # Random timestamp in the last 30 days
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                
                timestamp = datetime.now(timezone.utc) - timedelta(
                    days=days_ago,
                    hours=hours_ago,
                    minutes=minutes_ago
                )
                
                # Parse user agent to get device info
                user_agent = random.choice(USER_AGENTS)
                from utils import parse_user_agent
                device_info = parse_user_agent(user_agent)
                
                # Create click
                click = Click(
                    url_id=url.id,
                    timestamp=timestamp,
                    referrer=random.choice(REFERRERS),
                    user_agent=user_agent,
                    ip_address=random.choice(IP_ADDRESSES),
                    device_type=device_info["device_type"],
                    browser=device_info["browser"],
                    os=device_info["os"]
                )
                db.add(click)
            
            print(f"   📊 Added {num_clicks} clicks\n")
        
        db.commit()
        print("✨ Test data generated successfully!")
        print(f"\n📈 Created 10 URLs with random clicks")
        print(f"🔗 Try viewing stats: http://localhost:8000/stats/000001")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error generating test data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  TinyURL Test Data Generator")
    print("=" * 60)
    print()
    
    # Ask for confirmation
    response = input("⚠️  This will add test data to your database. Continue? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        generate_test_data()
    else:
        print("❌ Cancelled.")

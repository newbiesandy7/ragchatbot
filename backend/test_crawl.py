import httpx
from bs4 import BeautifulSoup

url = "https://bostoncollege.edu.np/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    print("🛰️ Attempting to reach the college home page...")
    res = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
    print(f"📊 Response Status Code: {res.status_code}")
    print(f"📋 Content Type Headers: {res.headers.get('content-type')}")
    
    soup = BeautifulSoup(res.text, 'html.parser')
    page_title = soup.title.string if soup.title else "No Title Found"
    print(f"🏷️ Scraped Page Title: {page_title}")
    
except Exception as e:
    print(f"❌ Connection failed instantly: {e}")
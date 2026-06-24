import asyncio
import httpx
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- CONFIGURATIONS ---
START_URL = "https://bostoncollege.edu.np/"
ALLOWED_DOMAIN = "bostoncollege.edu.np"
MAX_PAGES_TO_CRAWL = 30  

EMBEDDER_URL = "http://127.0.0.1:8001/embed"
LOCAL_DB_FILE = "campus_knowledge_base.json"

visited_urls = set()
urls_to_crawl = [START_URL]

def clean_and_chunk_html(html_content, url):
    """Strips navigation boilerplate and builds title-enriched content chunks."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for element in soup(["header", "footer", "nav", "sidebar", "script", "style", "noscript"]):
        element.decompose()
        
    page_title = soup.title.string.strip() if soup.title else "Boston International College Page"
    main_content = soup.find(['main', 'article', 'div'], id=['content', 'main']) or soup.body
    if not main_content:
        return []
        
    paragraphs = []
    for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'li', 'tr']):
        text = " ".join(p.get_text().split())
        if len(text) > 40: 
            paragraphs.append(text)
            
    chunks = []
    current_chunk = []
    current_length = 0
    for para in paragraphs:
        current_chunk.append(para)
        current_length += len(para)
        if current_length >= 600:
            combined_text = " ".join(current_chunk)
            chunks.append(f"Context Source: {page_title} ({url}) | Information: {combined_text}")
            current_chunk = []
            current_length = 0
            
    if current_chunk:
        combined_text = " ".join(current_chunk)
        chunks.append(f"Context Source: {page_title} ({url}) | Information: {combined_text}")
    return chunks

async def save_to_local_file_db(chunks, embeddings, source_url):
    """Appends vector items directly into a local JSON file matrix repository."""
    # Read existing database entries if they exist
    if os.path.exists(LOCAL_DB_FILE):
        with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
            try:
                database = json.load(f)
            except:
                database = []
    else:
        database = []

    # Map raw content rows side-by-side with vector matrix coordinates
    for chunk, vector in zip(chunks, embeddings):
        database.append({
            "vector": vector,
            "filename": source_url,
            "text": chunk
        })

    # Save tracking file block directly to storage disk
    with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 Saved {len(chunks)} text items locally inside '{LOCAL_DB_FILE}'")

async def process_text_chunks(chunks, source_url):
    if not chunks:
        return
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(EMBEDDER_URL, json={"texts": chunks})
            res.raise_for_status()
            embeddings = res.json()["embeddings"]
            
            # Send arrays to be saved inside file rows directly
            await save_to_local_file_db(chunks, embeddings, source_url)
        except Exception as e:
            print(f"   ❌ Data compilation processing error: {str(e)}")

async def crawl_and_index():
    # Reset old data targets before beginning a clean crawl
    if os.path.exists(LOCAL_DB_FILE):
        os.remove(LOCAL_DB_FILE)
        
    print(f"🚀 Starting Local File Scraper Pipeline at: {START_URL}")
    async with httpx.AsyncClient() as client:
        while urls_to_crawl and len(visited_urls) < MAX_PAGES_TO_CRAWL:
            current_url = urls_to_crawl.pop(0)
            if current_url in visited_urls:
                continue
                
            print(f"\n🕷️ Scraped Node ({len(visited_urls) + 1}/{MAX_PAGES_TO_CRAWL}): {current_url}")
            visited_urls.add(current_url)
            
            try:
                browser_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                response = await client.get(current_url, timeout=10.0, headers=browser_headers, follow_redirects=True)
                if response.status_code != 200 or "text/html" not in response.headers.get("content-type", ""):
                    continue
                
                chunks = clean_and_chunk_html(response.text, current_url)
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    full_url = urljoin(current_url, href)
                    parsed_url = urlparse(full_url)
                    if parsed_url.netloc == ALLOWED_DOMAIN and full_url not in visited_urls and full_url not in urls_to_crawl:
                        if not any(full_url.endswith(ext) for ext in [".pdf", ".jpg", ".png", ".docx"]):
                            urls_to_crawl.append(full_url)
                            
                await process_text_chunks(chunks, current_url)
            except Exception as e:
                print(f"❌ Skipped {current_url} due to error: {e}")

    print(f"\n🏁 Finished! Your database file is compiled inside '{LOCAL_DB_FILE}'")

if __name__ == "__main__":
    asyncio.run(crawl_and_index())
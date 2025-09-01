# src/your_project/config.py

# --- LLM Settings ---
LLM_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "nomic-embed-text"

# --- Wikipedia Settings ---
WIKI_BASE_URL = "https://{lang}.wikipedia.org"
WIKI_SEARCH_PATH = "/w/index.php?search={query}&ns0=1"
WIKI_URL_PATTERN = r"^https:\/\/[a-z]{2,3}\.wikipedia\.org\/wiki\/[\w%\-()]+$"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0 Safari/537.36"
    )
}

# --- FAISS Settings ---
RETRIEVER_K = 20

# --- Streamlit Settings ---
APP_TITLE = "Wikipedia Article Discussor"

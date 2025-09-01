import re
import json
import requests
from typing import Dict, List
from bs4 import BeautifulSoup
import streamlit as st
import nltk
from nltk.tokenize import sent_tokenize
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_core.tools import tool
from config import REQUEST_HEADERS, WIKI_URL_PATTERN, RETRIEVER_K,EMBEDDING_MODEL

# Ensure tokenizer available (safe to call multiple times)
nltk.download("punkt", quiet=True)

# Embeddings model
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)


@tool
def search_wikipedia_article(language_code:str, keyword:str) -> str:
    """
    Search Wikipedia for articles by keyword in a specific language edition.

    Args:
        language_code (str): Wikipedia language code (e.g., "en", "fr", "de").
        keyword (str): The search keyword. Spaces will be replaced with "+" to
            form a valid query string.

    Behavior:
        - Builds a Wikipedia search URL in the format:
            https://<language_code>.wikipedia.org/w/index.php?search=<keyword>&ns0=1
        - Sends a GET request to perform the search.
        - If the search directly redirects to a single article:
            * Returns the final article URL.
        - Otherwise:
            * Parses the search result page.
            * Extracts article titles and links from
              <div class="mw-search-result-heading">.
            * Formats them into a newline-separated string, e.g.:
                Title : URL
                Title : URL
                ...

    Returns:
        str: Either
            - The final article URL (if the search redirected directly),
            - Or a newline-separated list of "Title : URL" pairs representing
              search results.
    """

    url = f"https://{language_code}.wikipedia.org/w/index.php?search={keyword.replace(' ', '+')}&ns0=1"

    response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
    if response.history:
        return response.url

    soup = BeautifulSoup(response.text, "lxml")
    links = soup.select("div.mw-search-result-heading a")

    results = [
        f"{link.get_text(strip=True)} : https://{language_code}.wikipedia.org{link['href']}"
        for link in links
    ]
    return "\n".join(results) if results else "No results found."

@tool
def add_wikipedia_article(url : str) -> str:
    """
    Scrape and add Wikipedia article into directory.

    Args:
        url (str): Must follow this pattern:
                   https://<language_code>.wikipedia.org/wiki/<article>
                   Example: https://en.wikipedia.org/wiki/Python_(programming_language)

    What it does:
        - Validates that the URL is a proper Wikipedia article link.
        - Downloads the HTML of the page.
        - Extracts the main content paragraphs from <div class="mw-parser-output">.
        - Extracts infobox key-value pairs if available.
        - Stores data in st.session_state.data under the article ID:
            {
                "title": <article title>,
                "paragraph": [list of text paragraphs],
                "info": { infobox data as dict }
            }
        - Converts the scraped content into sentences, creates Document objects,
          and updates a FAISS vector store for semantic retrieval.

    Raises:
        RuntimeError: If the URL is invalid or no paragraphs were found.

    Side effects:
        - Updates st.session_state.data with the article content.
        - Updates st.session_state.vector_store with FAISS retriever.

    Returns:
        None. (All results are stored in Streamlit session state.)
    """
    session_state = st.session_state

    if not re.match(WIKI_URL_PATTERN, url):
        raise RuntimeError(f"Invalid Wikipedia URL: {url}")

    response = requests.get(url, headers=REQUEST_HEADERS, timeout=10).text
    soup = BeautifulSoup(response, "lxml")

    # Extract paragraphs
    content = soup.find("div", {"class": "mw-parser-output"})
    paragraphs: List[str] = [
        p.get_text(strip=True) for p in content.find_all("p") if p.get_text(strip=True)
    ] if content else []

    if not paragraphs:
        raise RuntimeError("No article content found.")

    # Extract infobox
    info: Dict[str, str] = {}
    infobox = soup.find("table", class_="infobox")
    if infobox:
        for row in infobox.find_all("tr"):
            header, value_cell = row.find("th"), row.find("td")
            if header and value_cell:
                key = header.get_text(" ", strip=True)
                value = value_cell.get_text(" ", strip=True)
                info[key] = value

    # Store in session state
    article_id = url.rsplit("/", 1)[-1]
    title = article_id.replace("_", " ")
    session_state.setdefault("data", {})
    session_state.setdefault("article_in_directory", [])

    session_state["data"][article_id] = {
        "title": title,
        "paragraph": paragraphs,
        "info": info,
    }

    # Build FAISS retriever
    dict_str = json.dumps(session_state["data"], indent=4)
    docs = [Document(page_content=sent) for sent in sent_tokenize(dict_str)]
    session_state["vector_store"] = FAISS.from_documents(docs, embeddings).as_retriever(
        search_kwargs={"k": RETRIEVER_K}
    )

    # Track stored articles
    session_state["article_in_directory"].append(title)
    return f"Articles in directory: {', '.join(session_state['article_in_directory'])}"

@tool
def searh_in_article(query : str) -> str:
    """
    use this to fetch valid information from article inside directory.

    Args:
        query (str): A user-provided query. 
                     Important: Rephrase questions into declarative statements 
                     before passing them here. 
                     For example:
                        - Instead of: "What are the health benefits of green tea?"
                        - Use: "The health benefits of green tea"

    Returns:
        str: Combined text content of the retrieved results.
    """
    session_state = st.session_state
    if not session_state.get("vector_store"):
        raise RuntimeError("No articles available. Please add one first.")

    results = session_state["vector_store"].invoke(query)
    return " ".join([result.page_content for result in results])
import pytest
from unittest.mock import patch, MagicMock
from service import scraper
import streamlit as st

@pytest.fixture(autouse=True)
def clear_session_state():
    """Ensure Streamlit session state is clean before each test."""
    st.session_state.clear()


def test_search_article_redirect():
    mock_response = MagicMock()
    mock_response.history = ["redirected"]
    mock_response.url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

    with patch("requests.get", return_value=mock_response):
        result = scraper.search_article("en", "Python")
        assert "https://en.wikipedia.org/wiki/Python" in result


def test_search_article_results():
    html = """
    <div class="mw-search-result-heading">
        <a href="/wiki/Test_Article">Test Article</a>
    </div>
    """
    mock_response = MagicMock()
    mock_response.history = []
    mock_response.text = html

    with patch("requests.get", return_value=mock_response):
        result = scraper.search_article("en", "Test")
        assert "Test Article" in result
        assert "https://en.wikipedia.org/wiki/Test_Article" in result


def test_add_wikipedia_article_invalid_url():
    with pytest.raises(RuntimeError):
        scraper.add_wikipedia_article("https://google.com/not_wiki")
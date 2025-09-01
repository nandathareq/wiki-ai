import streamlit as st
from typing import Callable, Dict, Any


def article_factory(data: Dict[str, Any]) -> Callable[[], None]:
    """
    Factory function that generates a Streamlit page for a given article.

    Args:
        data (dict): Dictionary containing article data.
            Expected keys:
                - "title" (str): The title of the article.
                - "paragraph" (list[str]): List of article paragraphs.

    Returns:
        Callable: A function that renders the article page when called.
    """
    def article() -> None:
        st.header(data.get("title", "Untitled Article"))

        paragraphs = data.get("paragraph", [])
        if not paragraphs:
            st.warning("This article has no content.")
        else:
            for paragraph in paragraphs:
                st.write(paragraph)

    return article

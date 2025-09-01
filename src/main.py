import streamlit as st
from pages.article import article_factory
from service.llm import system_prompt

def init_session_state():
    defaults = {
        "data": {},
        "messages": [{"role": "system", "content": system_prompt}],
        "vector_store": None,
        "article_in_directory": [],
        "is_tool_called": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


if("data" not in st.session_state):
    init_session_state()

# --- Page Definitions ---
pages = {
    "Chat": [st.Page("pages/chat.py", title="Chat")],
    "Article": [],
}

# --- Dynamic Article Pages ---
for data_value in st.session_state.data.values():
    article = article_factory(data_value)
    pages["Article"].append(
        st.Page(
            article,
            title=data_value["title"],
            url_path=data_value["title"].replace(" ", "-"),
        )
    )

# --- Navigation ---
pg = st.navigation(pages)
pg.run()

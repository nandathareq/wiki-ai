import time
import streamlit as st
from service.llm import response_generator, init_llm
from service.scraper import init_embeddings
from config import APP_TITLE, LLM_ENGINE

# --- UI Setup ---
st.title(APP_TITLE)


# --- Utility Functions ---

@st.dialog("Input LLM Engine URL")
def set_llm_url():
    st.write(f"open and run this collab {LLM_ENGINE}")
    url = st.text_input("paste url here ..")
    if st.button("Submit"):
        init_embeddings(url)
        init_llm(url)
        st.rerun()


def notify_start(tool_name: str) -> None:
    """Notify when a tool call starts."""
    st.session_state.is_tool_called = True
    st.toast(f"Calling tool: {tool_name}", icon="🚀")


def notify_finished() -> None:
    """Notify when tool execution finishes."""
    st.toast("Finished executing", icon="✅")


def notify_error(reason: str) -> None:
    """Notify when a tool call fails."""
    st.toast(f"Error: {reason}", icon="💔")

def handle_user_input():
    if prompt := st.chat_input("What do you want to know?"):
        
        if not st.session_state.llm:
            set_llm_url()
            return

        # Add user message
        st.session_state["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Stream assistant response
        with st.chat_message("assistant"):
            response = st.write_stream(
                response_generator(
                    st.session_state["messages"],
                    onstart=notify_start,
                    onfinished=notify_finished,
                    onerror=notify_error,
                )
            )

        # Store assistant response
        st.session_state["messages"].append({"role": "assistant", "content": response})

        # If tool was called, refresh after short delay
        if st.session_state.get("is_tool_called", False):
            time.sleep(1)
            st.rerun()

# --- Render Previous Messages ---
for message in st.session_state["messages"]:
    if message["role"] == "system":
        continue

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle New User Input ---
handle_user_input()
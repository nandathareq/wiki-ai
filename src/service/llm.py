import json
from typing import Any, Callable, Dict, Generator, List, Optional
from langchain_ollama import ChatOllama
from config import LLM_MODEL
from service.scraper import (
    add_wikipedia_article,
    search_wikipedia_article,
    searh_in_article,
)


# --- Model Setup ---
chat = ChatOllama(model=LLM_MODEL)


# --- Tools ---
tools = {t.name: t for t in [add_wikipedia_article, search_wikipedia_article, searh_in_article]}
tools_description = [
    {"name": tool.name, "description": tool.description, "args": tool.args}
    for tool in tools.values()
]

system_prompt = f"""
    You are a **Wikipedia Discussion Agent**.  
    Your role is to help discuss and explain topics as if they were part of a collaborative Wikipedia conversation.  

    ### Rules of Engagement:
    - Only respond if you can verify the information from retrieved sources.
    - Do not make things up.  
    - Prefer clear, factual, and neutral explanations, just like in Wikipedia discussions.  
    - When additional information is needed, you may use the available tools.
    - Do not repeat what tool returns

    ### Available Tools:
    {json.dumps(tools_description, indent=2)}

    ### Tool Usage:
    - **Do not** mix another string into paramater
    - If you need to use a tool, respond **only** in the following JSON format:
    {{
        "tool": "<tool_name>",
        "args": {{...}}
    }}

    ### directory:
    - You can also search information using wikipedia search engine.
    - You can scrape Wikipedia pages and add their contents to directory.    

    ### Goal:
    - Facilitate discussion and provide reliable, Wikipedia-style knowledge.  
    - Keep responses concise, factual, and in a neutral tone.  
    - use the same language as user
    """


# --- Response Generator ---
def response_generator(
    context: List[Dict[str, Any]],
    onstart: Optional[Callable[[str], None]] = None,
    onfinished: Optional[Callable[[], None]] = None,
    onerror: Optional[Callable[[str], None]] = None,
) -> Generator[str, None, None]:
    """
    Stream responses from the LLM, handling tool usage if needed.

    Args:
        context (list[dict]): Conversation history (messages).
        onstart (callable, optional): Called when a tool starts.
        onfinished (callable, optional): Called when tool execution finishes.
        onerror (callable, optional): Called on errors.

    Yields:
        str: Streamed response tokens.
    """
    onstart = onstart or (lambda name: None)
    onfinished = onfinished or (lambda: None)
    onerror = onerror or (lambda reason: None)

    try:
        stream = chat.stream(context)
        first_chunk = next(stream, None)

        if not first_chunk or not first_chunk.content:
            return

        first_content = first_chunk.content

        # --- Tool invocation branch ---
        if first_content.strip().startswith("{"):
            buffer = first_content
            for chunk in stream:
                if chunk.content:
                    buffer += chunk.content

            try:
                tool_call = json.loads(buffer)
                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args", {})

                if tool_name in tools:
                    onstart(tool_name)

                    # Execute tool
                    try:
                        result = tools[tool_name].invoke(tool_args)
                    except Exception as e:
                        onerror(f"Tool execution failed: {e}")
                        return

                    # Update conversation
                    context.append({"role": "assistant", "content": buffer})
                    context.append(
                        {
                            "role": "system",
                            "content": f"Follow up with result: {result}",
                        }
                    )

                    # Continue model stream with updated context
                    stream = chat.stream(context)
                    for chunk in stream:
                        if chunk.content:
                            yield chunk.content
                    onfinished()
                else:
                    onerror(f"Unknown tool requested: {tool_name}")

            except json.JSONDecodeError:
                onerror("Failed to parse tool call JSON.")

        # --- Normal assistant response branch ---
        else:
            yield first_content
            for chunk in stream:
                if chunk.content:
                    yield chunk.content

    except Exception as e:
        onerror(f"Unexpected error: {e}")
"""
Personal Chef AI (Sous) — Streamlit app.

Local run:
    streamlit run app.py
"""

from __future__ import annotations

import base64
import mimetypes
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from tavily import TavilyClient

from how_it_works import render_how_it_works_page

APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env")

MODEL_OPTIONS: dict[str, tuple[str, str, str, bool]] = {
    "Gemini": (
        "google_genai",
        "gemini-2.5-flash-lite",
        "GOOGLE_API_KEY",
        True,
    ),
    "Groq — text (llama-3.3-70b)": (
        "groq",
        "llama-3.3-70b-versatile",
        "GROQ_API_KEY",
        False,
    ),
    "Groq — vision (llama-4-scout)": (
        "groq",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "GROQ_API_KEY",
        True,
    ),
}

SYSTEM_PROMPT = """
You are a personal chef. The user will give you a list of ingredients they have left over in their house.

Using the web search tool when available, search the web for recipes that can be made with the ingredients they have.

Return recipe suggestions and eventually the recipe instructions to the user, if requested.
"""

SUGGESTIONS = [
    "Leftover chicken and rice — dinner ideas?",
    "Eggs, spinach, and feta — something quick",
    "Pasta, garlic, olive oil, canned tomatoes",
    "Healthy lunch with avocado and chickpeas",
]

_agents: dict[str, Any] = {}


def _init_session() -> None:
    for key, value in {"messages": [], "pending_prompt": None}.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _env_key(env_var: str) -> str | None:
    value = os.environ.get(env_var, "").strip()
    return value or None


def _make_web_search_tool(api_key: str):
    client = TavilyClient(api_key=api_key)

    @tool
    def web_search(query: str) -> dict[str, Any]:
        """Search the web for recipes and cooking information."""
        return client.search(query)

    return web_search


def _get_chat_model(provider: str, model_name: str, api_key: str):
    if provider == "google_genai":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=model_name, api_key=api_key)
    raise ValueError(f"Unsupported provider: {provider}")


def _get_agent(model_label: str, use_search: bool):
    provider, model_name, env_var, _ = MODEL_OPTIONS[model_label]
    api_key = _env_key(env_var)
    if not api_key:
        raise ValueError(f"Missing {env_var}. Add it to .env or Streamlit secrets.")

    tools: list[Any] = []
    if use_search:
        tavily_key = _env_key("TAVILY_API_KEY")
        if not tavily_key:
            raise ValueError("Web search is on, but TAVILY_API_KEY is missing.")
        tools.append(_make_web_search_tool(tavily_key))

    cache_key = f"{provider}:{model_name}:{use_search}:{bool(tools)}"
    if cache_key not in _agents:
        _agents[cache_key] = create_agent(
            model=_get_chat_model(provider, model_name, api_key),
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
        )
    return _agents[cache_key]


def _model_supports_images(model_label: str) -> bool:
    return MODEL_OPTIONS[model_label][3]


def _to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block["text"]))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(part for part in parts if part) or str(content)
    return str(content)


def _build_message(
    text: str,
    image_bytes: bytes | None,
    image_name: str | None,
    supports_images: bool,
) -> HumanMessage:
    text = (text or "").strip()
    has_image = image_bytes is not None

    if has_image and not supports_images:
        raise ValueError(
            "This model does not support photos. Choose Gemini or Groq vision."
        )

    if not has_image:
        return HumanMessage(content=text)

    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime_type, _ = mimetypes.guess_type(image_name or "upload.jpg")
    mime_type = mime_type or "image/jpeg"

    prompt = text or "What can I make with the ingredients in this image?"
    return HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image", "base64": img_b64, "mime_type": mime_type},
        ]
    )


def _session_to_langchain_messages(
    messages: list[dict[str, Any]],
    supports_images: bool,
) -> list[HumanMessage | AIMessage]:
    lc_messages: list[HumanMessage | AIMessage] = []
    for msg in messages:
        if msg["role"] == "user":
            image_bytes = msg.get("image")
            text = msg["content"]
            if image_bytes and supports_images:
                img_b64 = base64.b64encode(image_bytes).decode("utf-8")
                lc_messages.append(
                    HumanMessage(
                        content=[
                            {"type": "text", "text": text},
                            {
                                "type": "image",
                                "base64": img_b64,
                                "mime_type": "image/jpeg",
                            },
                        ]
                    )
                )
            else:
                lc_messages.append(HumanMessage(content=text))
        else:
            lc_messages.append(AIMessage(content=msg["content"]))
    return lc_messages


def _invoke_chef(
    text: str,
    image_bytes: bytes | None,
    image_name: str | None,
    model_label: str,
    use_search: bool,
) -> str:
    supports_images = _model_supports_images(model_label)
    agent = _get_agent(model_label, use_search)

    history = list(st.session_state.messages[:-1])
    current_display = st.session_state.messages[-1]["content"]
    current_message = _build_message(
        text or current_display,
        image_bytes,
        image_name,
        supports_images,
    )
    lc_messages = _session_to_langchain_messages(history, supports_images)
    lc_messages.append(current_message)

    response = agent.invoke({"messages": lc_messages})
    return _to_text(response["messages"][-1].content)


def _reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.pending_prompt = None


def _render_sidebar() -> tuple[str, bool]:
    with st.sidebar:
        st.header("Settings")
        model_label = st.selectbox(
            "Model",
            options=list(MODEL_OPTIONS.keys()),
            help=(
                "Gemini & Groq vision support fridge photos. "
                "Groq text (llama-3.3-70b) is text-only but faster."
            ),
        )
        use_search = st.toggle("Search the web for recipes", value=True)
        if st.button("New conversation", use_container_width=True):
            _reset_chat()
            st.rerun()
    return model_label, use_search


def _handle_user_turn(
    text: str,
    image_bytes: bytes | None,
    image_name: str | None,
    model_label: str,
    use_search: bool,
) -> None:
    display_text = text.strip() or (
        "Uploaded a fridge photo — what can I make?" if image_bytes else ""
    )
    if not display_text and not image_bytes:
        return

    st.session_state.messages.append(
        {"role": "user", "content": display_text, "image": image_bytes}
    )

    with st.chat_message("user"):
        if image_bytes:
            st.image(image_bytes)
        st.markdown(display_text)

    with st.chat_message("assistant"):
        with st.spinner("Finding recipes..."):
            try:
                reply = _invoke_chef(
                    text, image_bytes, image_name, model_label, use_search
                )
            except Exception as exc:
                reply = f"Something went wrong: {exc}"
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})


def chat_page() -> None:
    _init_session()
    model_label, use_search = _render_sidebar()

    st.title("Sous")
    st.write(
        "Your AI personal chef. Tell me what's in your kitchen, "
        "or attach a fridge photo in the chat box below."
    )

    if not st.session_state.messages:
        st.subheader("Try an example")
        for index, suggestion in enumerate(SUGGESTIONS):
            if st.button(suggestion, key=f"example_{index}"):
                st.session_state.pending_prompt = suggestion
                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("image"):
                st.image(message["image"])
            st.markdown(message["content"])

    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        _handle_user_turn(prompt, None, None, model_label, use_search)

    chat_input = st.chat_input(
        "What ingredients do you have?",
        accept_file=True,
        file_type=["jpg", "jpeg", "png", "webp"],
    )

    if chat_input:
        image_bytes = None
        image_name = None
        if chat_input.files:
            uploaded = chat_input.files[0]
            image_bytes = uploaded.read()
            image_name = uploaded.name
        _handle_user_turn(
            chat_input.text or "",
            image_bytes,
            image_name,
            model_label,
            use_search,
        )


def run_app() -> None:
    st.set_page_config(page_title="Sous — Personal Chef AI", page_icon="🍳")

    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] li { margin-bottom: 0.5rem; }
        [data-testid="stSidebarNav"] span {
            font-size: 1.1rem !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] span {
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### 🍳 Sous")
        st.caption("Use the menu below to switch pages.")
        st.divider()

    chef_page = st.Page(chat_page, title="Chef", icon="🍳", default=True)
    how_page = st.Page(render_how_it_works_page, title="How it works", icon="ℹ️")
    st.navigation([chef_page, how_page]).run()


if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        in_streamlit = get_script_run_ctx() is not None
    except Exception:
        in_streamlit = False

    if not in_streamlit:
        cmd = [sys.executable, "-m", "streamlit", "run", str(APP_DIR / "app.py")]
        raise SystemExit(subprocess.call(cmd, cwd=APP_DIR))

    run_app()

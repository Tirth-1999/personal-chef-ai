"""How it works page — native Streamlit layout."""

from __future__ import annotations

import streamlit as st

STACK = [
    ("Streamlit", "Web UI, chat, file upload, hosting"),
    ("LangChain `create_agent`", "Agent loop: model + tools + system prompt"),
    ("LangGraph", "Runs the agent graph behind `create_agent`"),
    ("Gemini / Groq", "LLM providers — swap without rewriting the app"),
    ("Tavily", "Web search tool for real recipe links"),
    ("python-dotenv", "API keys from environment (local `.env` or Streamlit secrets)"),
]


def _render_architecture() -> None:
    st.subheader("Architecture")
    st.write(
        "Each message travels through these layers. Everything runs in one Python app — "
        "no separate backend server."
    )

    row1 = st.columns([3, 0.4, 3, 0.4, 3], gap="small")
    with row1[0]:
        with st.container(border=True):
            st.markdown("**① You**")
            st.caption("Type ingredients or attach a fridge photo in chat.")
    row1[1].markdown("### →")
    with row1[2]:
        with st.container(border=True):
            st.markdown("**② Streamlit UI**")
            st.caption("Shows chat, stores conversation history in the session.")
    row1[3].markdown("### →")
    with row1[4]:
        with st.container(border=True):
            st.markdown("**③ LangChain agent**")
            st.caption("`create_agent` + personal-chef system prompt.")

    st.markdown("")

    row2 = st.columns([3, 0.4, 3, 0.4, 3], gap="small")
    with row2[0]:
        with st.container(border=True):
            st.markdown("**④ LLM (pick in sidebar)**")
            st.markdown("- Gemini (text + photos)\n- Groq text\n- Groq vision")
    row2[1].markdown("### ↔")
    with row2[2]:
        with st.container(border=True):
            st.markdown("**⑤ Tavily tool** *(optional)*")
            st.caption("`web_search` — finds real recipes on the web when enabled.")
    row2[3].markdown("### →")
    with row2[4]:
        with st.container(border=True):
            st.markdown("**⑥ Reply**")
            st.caption("Agent returns recipe ideas or step-by-step instructions.")

    st.info(
        "**Model agnostic:** the agent code stays the same — only the model name "
        "in the sidebar changes (Gemini or Groq)."
    )


def _render_turn_one() -> None:
    with st.container(border=True):
        st.markdown("#### Turn 1 · Ask for recipe ideas")
        st.markdown(
            """
1. **You** send: *"I have chicken and rice"*
2. **Streamlit** adds it to the conversation and calls the agent
3. **Agent** asks the **LLM** what to do
4. **LLM** requests the **Tavily** `web_search` tool
5. **Tavily** returns recipe links and snippets from the web
6. **LLM** writes a helpful summary
7. **You** see recipe suggestions in the chat
            """
        )


def _render_turn_two() -> None:
    with st.container(border=True):
        st.markdown("#### Turn 2 · Follow-up (memory)")
        st.markdown(
            """
1. **You** send: *"Give me the full recipe for the first one"*
2. **Streamlit** sends the **full chat history** + your new message
3. **Agent** remembers the chicken & rice context from turn 1
4. **LLM** returns step-by-step cooking instructions
5. **You** see the detailed recipe — no need to repeat yourself
            """
        )


def _render_conversation_flow() -> None:
    st.subheader("One conversation — two turns")
    st.write(
        "When web search is on, turn 1 uses Tavily. Turn 2 uses **memory** — "
        "the entire conversation is sent again so the chef knows what you meant."
    )
    _render_turn_one()
    st.markdown("")
    _render_turn_two()


def render_how_it_works_page() -> None:
    st.title("How Sous works")
    st.write(
        "A LangChain agent demo: chat with a personal chef, search the web for recipes, "
        "upload fridge photos (on vision models), and continue the conversation with memory."
    )

    _render_architecture()
    st.divider()
    _render_conversation_flow()
    st.divider()

    st.subheader("Tech stack")
    for name, description in STACK:
        st.markdown(f"- **{name}** — {description}")

    st.subheader("Models you can pick")
    st.markdown(
        """
| Sidebar option | Provider | Best for |
|----------------|----------|----------|
| Gemini | Google | Text + fridge photos |
| Groq — text | Groq `llama-3.3-70b` | Fast text-only chat |
| Groq — vision | Groq `llama-4-scout` | Text + photos |
        """
    )

"""
streamlit_app.py
Main Streamlit app for the Podcast Q&A Bot.

Run with:
    streamlit run app/streamlit_app.py

Features:
  - Clean dark UI with custom typography
  - Full answer rendered as prose (not chunks)
  - YouTube video embedded directly in the page, auto-seeking to best timestamp
  - Source timestamp chips showing which parts of the podcast were used
  - Session history of past questions
"""

import sys
from pathlib import Path

# Make src importable when running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from src.answerer import ask
from app.components import (
    inject_global_styles,
    render_hero,
    render_answer,
    render_video,
    render_sources,
    render_not_found,
    render_history_item,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ask Elon × Nikhil",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

YOUTUBE_ID     = "Rni7Fz7208c"
INDEX_PATH     = "data/faiss_index.bin"
METADATA_PATH  = "data/chunk_metadata.pkl"

EXAMPLE_QUESTIONS = [
    "What probability does Elon ascribe to us living in a simulation, and what is his most interesting outcome theory?",
    "What core advice does Elon give to young ambitious entrepreneurs in India who want to build something?",
    "What are the three most important things for AI to have, and why is forcing an AI to lie so dangerous?",
    "What is Elon's prediction for the future of human work, and what is his specific timeframe for this change?",
]

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []   # list of {query, result}

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "current_query" not in st.session_state:
    st.session_state.current_query = ""

# ── Styles + Hero ─────────────────────────────────────────────────────────────
inject_global_styles()
render_hero()

# ── Input area ────────────────────────────────────────────────────────────────
query = st.text_input(
    label="question",
    placeholder="Ask anything from the podcast…",
    label_visibility="collapsed",
    key="query_input",
)

col1, col2 = st.columns([3, 1])
with col1:
    ask_clicked = st.button("Ask", use_container_width=True)
with col2:
    clear_clicked = st.button("Clear", use_container_width=True)

# Example question pills
st.markdown("<div style='margin: 0.5rem 0 1.5rem; display:flex; flex-wrap:wrap; gap:6px;'>", unsafe_allow_html=True)
for eq in EXAMPLE_QUESTIONS:
    if st.button(eq, key=f"eq_{eq}"):
        query = eq
        ask_clicked = True
st.markdown("</div>", unsafe_allow_html=True)

# ── Clear ─────────────────────────────────────────────────────────────────────
if clear_clicked:
    st.session_state.current_result = None
    st.session_state.current_query  = ""
    st.session_state.history        = []
    st.rerun()

# ── Handle query ──────────────────────────────────────────────────────────────
if ask_clicked and query and query.strip():
    with st.spinner("Searching the transcript…"):
        result = ask(
            query=query.strip(),
            top_k=5,
            index_path=INDEX_PATH,
            metadata_path=METADATA_PATH,
        )

    st.session_state.current_result = result
    st.session_state.current_query  = query.strip()

    # Prepend to history (most recent first)
    st.session_state.history.insert(0, {
        "query":  query.strip(),
        "result": result,
    })

# ── Render current result ─────────────────────────────────────────────────────
result = st.session_state.current_result

if result is not None:
    if result.get("not_found"):
        render_not_found()
    else:
        # 1. Prose answer card
        render_answer(result)

        # 2. Embedded YouTube player at exact timestamp
        render_video(
            youtube_id=YOUTUBE_ID,
            start_sec=result["timestamp_sec"],
        )

        # 3. Source timestamp chips
        render_sources(result.get("sources", []))

# ── History ───────────────────────────────────────────────────────────────────
if len(st.session_state.history) > 1:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-family:Syne,sans-serif; font-size:10px; font-weight:700; "
        "letter-spacing:0.16em; text-transform:uppercase; color:#5A5A72; margin-bottom:1rem;'>"
        "Previous Questions</div>",
        unsafe_allow_html=True,
    )
    # Skip index 0 (the current one already rendered above)
    for item in st.session_state.history[1:6]:
        render_history_item(
            q=item["query"],
            a=item["result"].get("answer", ""),
        )
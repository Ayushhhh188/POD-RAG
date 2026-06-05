"""
components.py
Reusable UI helpers for streamlit_app.py.
Keeps all HTML/CSS injection isolated so the main app stays clean.
"""

import streamlit as st
from src.youtube_utils import seconds_to_timestamp, format_source_label


def inject_global_styles():
    """Inject all custom CSS for the app."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

    /* ── Reset & base ── */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0C0C0F !important;
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stSidebar"] { display: none; }
    .block-container {
        max-width: 860px !important;
        padding: 2rem 2rem 4rem !important;
    }

    /* ── Hero header ── */
    .hero {
        text-align: center;
        padding: 3rem 0 2.5rem;
        border-bottom: 1px solid #1E1E24;
        margin-bottom: 2.5rem;
    }
    .hero-eyebrow {
        font-family: 'DM Sans', sans-serif;
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #5A5A72;
        margin-bottom: 0.75rem;
    }
    .hero-title {
        font-family: 'Syne', sans-serif;
        font-size: clamp(2rem, 5vw, 3.2rem);
        font-weight: 800;
        line-height: 1.1;
        color: #F0EEF8;
        letter-spacing: -0.02em;
        margin-bottom: 0.6rem;
    }
    .hero-title span {
        color: #7B61FF;
    }
    .hero-sub {
        font-size: 14px;
        color: #5A5A72;
        font-weight: 300;
    }

    /* ── Search bar ── */
    .stTextInput > div > div > input {
        background: #13131A !important;
        border: 1px solid #2A2A38 !important;
        border-radius: 12px !important;
        color: #F0EEF8 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 15px !important;
        padding: 0.85rem 1.2rem !important;
        transition: border-color 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #7B61FF !important;
        box-shadow: 0 0 0 3px rgba(123,97,255,0.12) !important;
    }
    .stTextInput > div > div > input::placeholder { color: #3A3A52 !important; }

    /* ── Ask button ── */
    .stButton > button {
        background: #7B61FF !important;
        color: #fff !important;
        border: none !important;
        border-radius: 12px !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.04em !important;
        padding: 0.85rem 2rem !important;
        width: 100% !important;
        transition: background 0.2s ease, transform 0.1s ease !important;
    }
    .stButton > button:hover {
        background: #6B4FEF !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* ── Answer card ── */
    .answer-card {
        background: #13131A;
        border: 1px solid #2A2A38;
        border-radius: 16px;
        padding: 1.75rem 2rem;
        margin: 1.5rem 0;
        position: relative;
    }
    .answer-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #7B61FF, #B49DFF);
        border-radius: 16px 16px 0 0;
    }
    .answer-label {
        font-family: 'Syne', sans-serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #7B61FF;
        margin-bottom: 0.85rem;
    }
    .answer-text {
        font-size: 15px;
        font-weight: 400;
        line-height: 1.75;
        color: #C8C4DC;
    }
    .confidence-badge {
        display: inline-block;
        margin-top: 1rem;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.06em;
    }
    .conf-high   { background: rgba(52,199,89,0.12);  color: #34C759; }
    .conf-medium { background: rgba(255,179,0,0.12);  color: #FFB300; }
    .conf-low    { background: rgba(255,69,58,0.12);  color: #FF453A; }

    /* ── Video section ── */
    .video-label {
        font-family: 'Syne', sans-serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #5A5A72;
        margin: 2rem 0 0.75rem;
    }
    .video-wrapper {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #2A2A38;
        background: #000;
    }

    /* ── Sources ── */
    .sources-header {
        font-family: 'Syne', sans-serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #5A5A72;
        margin: 2rem 0 0.75rem;
    }
    .source-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #13131A;
        border: 1px solid #2A2A38;
        border-radius: 8px;
        padding: 6px 12px;
        margin: 0 6px 6px 0;
        font-size: 12px;
        color: #7B7B9A;
        cursor: default;
    }
    .source-chip-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #7B61FF;
        flex-shrink: 0;
    }

    /* ── Not found state ── */
    .not-found {
        background: #13131A;
        border: 1px dashed #2A2A38;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        color: #5A5A72;
        font-size: 14px;
        margin: 1.5rem 0;
    }

    /* ── History item ── */
    .history-item {
        border-left: 2px solid #2A2A38;
        padding: 0.5rem 0 0.5rem 1rem;
        margin-bottom: 1rem;
    }
    .history-q {
        font-size: 12px;
        color: #7B61FF;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .history-a {
        font-size: 13px;
        color: #5A5A72;
        line-height: 1.5;
    }

    /* ── Divider ── */
    hr { border-color: #1E1E24 !important; margin: 2rem 0 !important; }

    /* ── Spinner ── */
    [data-testid="stSpinner"] p { color: #5A5A72 !important; font-size: 13px !important; }
    </style>
    """, unsafe_allow_html=True)


def render_hero():
    st.markdown("""
    <div class="hero">
        <div class="hero-eyebrow">People by WTF · Episode 16</div>
        <div class="hero-title">Ask <span>Elon × Nikhil</span></div>
        <div class="hero-sub">Questions answered from the podcast transcript · jumps to the exact moment</div>
    </div>
    """, unsafe_allow_html=True)


def render_answer(result: dict):
    """Render the answer card with confidence badge."""
    confidence = result.get("confidence", "medium")
    conf_class = f"conf-{confidence}"

    # Sanitise before HTML injection — backslash-escaped quotes from JSON
    # corrupt the div when injected raw into the f-string
    answer_text = result['answer']
    answer_text = answer_text.replace('\\"', '"').replace("\\'", "'")
    answer_text = answer_text.replace("\\n", "<br>").replace("\n", "<br>")

    st.markdown(f"""
    <div class="answer-card">
        <div class="answer-label">Answer</div>
        <div class="answer-text">{answer_text}</div>
        <span class="confidence-badge {conf_class}">
            {confidence.upper()} CONFIDENCE
        </span>
    </div>
    """, unsafe_allow_html=True)



def render_video(youtube_id: str, start_sec: float):
    """Render embedded YouTube player starting at start_sec."""
    from src.youtube_utils import seconds_to_embed_url, seconds_to_timestamp

    embed_url   = seconds_to_embed_url(youtube_id, start_sec)
    timestamp   = seconds_to_timestamp(start_sec)

    st.markdown('<div class="video-label">▶ Watch in context</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="video-wrapper">'
        f'<iframe width="100%" height="420" src="{embed_url}" '
        f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
        f'encrypted-media; gyroscope; picture-in-picture" allowfullscreen>'
        f'</iframe></div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Starting at {timestamp}")


def render_sources(chunks: list[dict]):
    """Render source timestamp chips below the video."""
    if not chunks:
        return

    st.markdown('<div class="sources-header">Sources used</div>', unsafe_allow_html=True)

    chips_html = ""
    for chunk in chunks:
        label = format_source_label(chunk["start_sec"], chunk["end_sec"])
        score = chunk.get("score", 0)
        chips_html += (
            f'<span class="source-chip">'
            f'<span class="source-chip-dot"></span>'
            f'{label} &nbsp;·&nbsp; {score:.2f}'
            f'</span>'
        )

    st.markdown(chips_html, unsafe_allow_html=True)


def render_not_found():
    st.markdown("""
    <div class="not-found">
        This topic wasn't found in the transcript excerpts retrieved.<br>
        Try rephrasing your question or asking about something else from the podcast.
    </div>
    """, unsafe_allow_html=True)


def render_history_item(q: str, a: str):
    short_a = a[:140] + "..." if len(a) > 140 else a
    st.markdown(f"""
    <div class="history-item">
        <div class="history-q">Q: {q}</div>
        <div class="history-a">{short_a}</div>
    </div>
    """, unsafe_allow_html=True)
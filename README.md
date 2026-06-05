# Podcast Q&A Bot 🎙️
> Ask questions about the **Elon Musk × Nikhil Kamath** interview (People by WTF, Ep. 16) — get grounded answers with the video jumping to the exact timestamp.

---

## How it works

```
audio.mp3 → Whisper → chunks → SentenceTransformer → FAISS → Gemini 3.5 Flash → Streamlit
```

1. **Transcribe** — Whisper (medium) transcribes the podcast with timestamps
2. **Chunk** — transcript split into 45s windows (10s overlap)
3. **Embed** — `all-MiniLM-L6-v2` embeds chunks locally → FAISS index
4. **Query** — question embedded → top-5 cosine search → Gemini answers → video jumps to timestamp

---

## Setup

```bash
git clone https://github.com/yourname/podcast-qa-bot
cd podcast-qa-bot
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Create `.env` in the project root:
```
GOOGLE_API_KEY=your_key_here
```
Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)

Install FFmpeg: `winget install --id Gyan.FFmpeg` (Windows) or `brew install ffmpeg` (Mac)

---

## Run

**Step 1 — place audio** at `data/audio.mp3` (download manually from YouTube)

**Step 2 — ingest** (run once):
```bash
python pipeline/ingest.py --skip-download
```

**Step 3 — launch:**
```bash
streamlit run app/streamlit_app.py
```

---

## Stack

| Layer | Tool |
|---|---|
| Transcription | OpenAI Whisper (local) |
| Embeddings | SentenceTransformer `all-MiniLM-L6-v2` (local) |
| Vector store | FAISS `IndexFlatIP` |
| Generation | Gemini 3.5 Flash |
| UI | Streamlit + custom CSS |

---

## Project structure

```
src/          # downloader, transcriber, chunker, embedder, retriever, answerer, youtube_utils
pipeline/     # ingest.py — one-shot ingestion orchestrator
app/          # streamlit_app.py, components.py
data/         # gitignored — audio, transcript, chunks, FAISS index
```

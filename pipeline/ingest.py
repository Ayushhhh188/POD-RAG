"""
pipeline/ingest.py
One-shot ingestion pipeline. Run this once per podcast.

Steps:
  1. Download audio from YouTube          → data/audio.mp3
  2. Transcribe with Whisper              → data/transcript_raw.json
  3. Chunk transcript (45s windows)       → data/chunks.json
  4. Embed chunks with SentenceTransformer → data/faiss_index.bin
                                           data/chunk_metadata.pkl

Usage:
    python pipeline/ingest.py                           # full pipeline
    python pipeline/ingest.py --skip-download           # audio.mp3 already exists
    python pipeline/ingest.py --skip-transcribe         # transcript already exists
    python pipeline/ingest.py --skip-download --skip-transcribe   # jump straight to chunk+embed
    python pipeline/ingest.py --model large-v3          # use larger whisper model
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.downloader  import download_audio
from src.transcriber import transcribe
from src.chunker     import chunk_transcript
from src.embedder    import build_faiss_index

YOUTUBE_URL = "https://youtu.be/Rni7Fz7208c?si=7aPMltN1nZZFHRlJ"
YOUTUBE_ID  = "Rni7Fz7208c"


def run(
    youtube_url:      str  = YOUTUBE_URL,
    youtube_id:       str  = YOUTUBE_ID,
    skip_download:    bool = False,
    skip_transcribe:  bool = False,
    whisper_model:    str  = "medium",
):
    print("=" * 60)
    print("  Podcast Q&A Bot — Ingestion Pipeline")
    print("=" * 60)

    # ── Step 1: Download ──────────────────────────────────────────
    audio_path = Path("data/audio.mp3")

    if skip_download or audio_path.exists():
        size_mb = audio_path.stat().st_size / (1024 * 1024) if audio_path.exists() else 0
        print(f"\n[step 1/4] Skipping download — audio.mp3 exists ({size_mb:.1f} MB)")
    else:
        print(f"\n[step 1/4] Downloading audio...")
        download_audio(youtube_url, str(audio_path))

    # ── Step 2: Transcribe ────────────────────────────────────────
    transcript_path = Path("data/transcript_raw.json")

    if skip_transcribe or transcript_path.exists():
        print(f"\n[step 2/4] Skipping transcription — transcript_raw.json exists")
    else:
        print(f"\n[step 2/4] Transcribing with Whisper ({whisper_model})...")
        transcribe(
            audio_path=str(audio_path),
            output_path=str(transcript_path),
            model_name=whisper_model,
            youtube_id=youtube_id,
        )

    # ── Step 3: Chunk ─────────────────────────────────────────────
    chunks_path = Path("data/chunks.json")

    if chunks_path.exists():
        print(f"\n[step 3/4] Skipping chunking — chunks.json exists")
        print(f"           Delete it to force re-chunk.")
    else:
        print(f"\n[step 3/4] Chunking transcript...")
        chunk_transcript(
            input_path=str(transcript_path),
            output_path=str(chunks_path),
        )

    # ── Step 4: Embed ─────────────────────────────────────────────
    index_path = Path("data/faiss_index.bin")
    metadata_path = Path("data/chunk_metadata.pkl")

    if index_path.exists() and metadata_path.exists():
        print(
            "\n[step 4/4] Skipping embedding — "
            "faiss_index.bin + chunk_metadata.pkl exist"
        )
        print("           Delete them to force re-embed.")
    else:
        print(
            "\n[step 4/4] Embedding chunks with "
            "SentenceTransformer..."
        )

        build_faiss_index(
            input_path=str(chunks_path),
            index_path=str(index_path),
            metadata_path=str(metadata_path),
        )

    # ── Done ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Ingestion complete. Ready to query.")
    print("  Run: streamlit run app/streamlit_app.py")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a podcast for Q&A")
    parser.add_argument("--url",              default=YOUTUBE_URL)
    parser.add_argument("--youtube-id",       default=YOUTUBE_ID)
    parser.add_argument("--skip-download",    action="store_true")
    parser.add_argument("--skip-transcribe",  action="store_true")
    parser.add_argument("--model",            default="medium")
    args = parser.parse_args()

    run(
    youtube_url=args.url,
    youtube_id=args.youtube_id,
    skip_download=args.skip_download,
    skip_transcribe=args.skip_transcribe,
    whisper_model=args.model,
)
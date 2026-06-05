"""
chunker.py
Reads transcript_raw.json and groups Whisper segments into overlapping
time-windows suitable for embedding and retrieval.

Why chunk at all?
- Whisper segments are 2-10s each — too short for meaningful embedding
- We want ~45s windows so each chunk covers a complete thought/topic
- 10s overlap ensures sentences at boundaries appear in two chunks,
  so nothing gets lost at the seam

Output schema (chunks.json):
[
  {
    "chunk_id": 0,
    "start_sec": 30.0,
    "end_sec": 75.4,
    "text": "Our audience is largely wannabe entrepreneurs ...",
    "youtube_id": "oOcVLVlSqBQ",
    "youtube_url": "https://www.youtube.com/watch?v=oOcVLVlSqBQ&t=30s"
  },
  ...
]
"""

import json
import sys
from pathlib import Path


CHUNK_DURATION   = 45   # seconds per chunk
OVERLAP_DURATION = 10   # seconds of overlap between consecutive chunks


def seconds_to_hhmmss(seconds: float) -> str:
    """Convert float seconds to HH:MM:SS string for logging."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_youtube_url(youtube_id: str, start_sec: float) -> str:
    """Return a deep-link URL that starts playback at start_sec."""
    return f"https://www.youtube.com/watch?v={youtube_id}&t={int(start_sec)}s"


def chunk_transcript(
    input_path:  str = "data/transcript_raw.json",
    output_path: str = "data/chunks.json",
    chunk_duration:   int = CHUNK_DURATION,
    overlap_duration: int = OVERLAP_DURATION,
) -> list[dict]:
    """
    Groups Whisper segments into overlapping time-window chunks.

    Args:
        input_path:       Path to transcript_raw.json
        output_path:      Where to write chunks.json
        chunk_duration:   Target length of each chunk in seconds (default 45)
        overlap_duration: Overlap between consecutive chunks in seconds (default 10)

    Returns:
        List of chunk dicts (same as written to disk).
    """
    raw_path = Path(input_path)
    if not raw_path.exists():
        raise FileNotFoundError(
            f"Transcript not found: {raw_path}\n"
            "Run transcriber.py first."
        )

    data     = json.loads(raw_path.read_text(encoding="utf-8"))
    segments = data["segments"]
    youtube_id = data.get("youtube_id", "")
    total_duration = data.get("duration_seconds", 0)

    print(f"[chunker] Loaded {len(segments)} segments "
          f"({seconds_to_hhmmss(total_duration)} total)")
    print(f"[chunker] Chunking with window={chunk_duration}s, overlap={overlap_duration}s")

    chunks   = []
    chunk_id = 0
    step     = chunk_duration - overlap_duration   # how far to advance each time

    # Walk through the timeline in steps, collecting all segments that fall
    # within [window_start, window_start + chunk_duration]
    window_start = segments[0]["start"] if segments else 0.0

    while window_start < total_duration:
        window_end = window_start + chunk_duration

        # Collect segments whose start time falls inside this window
        window_segs = [
            seg for seg in segments
            if window_start <= seg["start"] < window_end
        ]

        if not window_segs:
            window_start += step
            continue

        text       = " ".join(seg["text"].strip() for seg in window_segs)
        actual_end = window_segs[-1]["end"]

        chunk = {
            "chunk_id":   chunk_id,
            "start_sec":  round(window_segs[0]["start"], 2),
            "end_sec":    round(actual_end, 2),
            "text":       text.strip(),
            "youtube_id": youtube_id,
            "youtube_url": build_youtube_url(youtube_id, window_segs[0]["start"]),
        }

        chunks.append(chunk)
        chunk_id    += 1
        window_start += step

    # Write output
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")

    avg_len = sum(len(c["text"].split()) for c in chunks) / max(len(chunks), 1)
    print(f"[chunker] Created {len(chunks)} chunks "
          f"(avg {avg_len:.0f} words each) → {out}")

    return chunks


if __name__ == "__main__":
    chunk_transcript()
"""
transcriber.py
Transcribes audio using OpenAI Whisper (runs locally, no API key needed).
Produces transcript_raw.json with full segment-level timestamps.

Output schema (transcript_raw.json):
{
  "youtube_id": "oOcVLVlSqBQ",
  "language": "en",
  "duration_seconds": 3847.2,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 4.52,
      "text": " So Elon, you've said that you don't really enjoy interviews...",
      "avg_logprob": -0.23,
      "no_speech_prob": 0.01
    },
    ...
  ]
}
"""

import json
import os
import sys
import time
from pathlib import Path

# ── Windows FFmpeg PATH fix ───────────────────────────────────────────────────
# Whisper calls ffmpeg as a subprocess. On Windows the venv often doesn't
# inherit the system PATH correctly. We try common install locations and
# prepend whichever one exists. Safe to leave in on Mac/Linux - won't match.
_FFMPEG_CANDIDATES = [
    r"C:\Users\ayush\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin",
    r"C:\Program Files\ffmpeg\bin",
    r"C:\ffmpeg\bin",
    r"C:\ProgramData\chocolatey\bin",
    r"C:\tools\ffmpeg\bin",
]
for _p in _FFMPEG_CANDIDATES:
    if Path(_p).exists() and _p not in os.environ["PATH"]:
        os.environ["PATH"] = _p + os.pathsep + os.environ["PATH"]
        print(f"[transcriber] Added ffmpeg to PATH: {_p}")
        break
# ─────────────────────────────────────────────────────────────────────────────

import whisper


# Model sizes: tiny, base, small, medium, large-v3
# large-v3 is most accurate but ~10GB and slow without GPU.
# "medium" is the best CPU trade-off for a ~1hr podcast.
DEFAULT_MODEL = "medium"


def transcribe(
    audio_path: str = "data/audio.mp3",
    output_path: str = "data/transcript_raw.json",
    model_name: str = DEFAULT_MODEL,
    youtube_id: str = "oOcVLVlSqBQ",
) -> dict:
    """
    Runs Whisper on the audio file and saves transcript_raw.json.

    Args:
        audio_path:   Path to the mp3 file.
        output_path:  Where to write the JSON output.
        model_name:   Whisper model size (tiny/base/small/medium/large-v3).
        youtube_id:   The YouTube video ID — stored in the JSON for deep-link use.

    Returns:
        The full transcript dict (same as what's written to disk).
    """
    audio = Path(audio_path)
    if not audio.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio}\n"
            "Run pipeline/ingest.py first, or place audio.mp3 in the data/ folder."
        )

    print(f"[transcriber] Loading Whisper model: {model_name} (downloads on first run)")
    t0 = time.time()
    model = whisper.load_model(model_name)
    print(f"[transcriber] Model loaded in {time.time() - t0:.1f}s")

    print(f"[transcriber] Transcribing {audio} — this takes a few minutes...")
    t1 = time.time()

    result = model.transcribe(
        str(audio),
        language="en",           # skip auto-detection, saves time
        verbose=True,            # prints segments as they complete
        word_timestamps=False,   # segment-level is enough; word-level is slow
        fp16=False,              # safer on CPU-only machines
        condition_on_previous_text=True,
    )

    elapsed = time.time() - t1
    print(f"[transcriber] Transcription complete in {elapsed:.0f}s")

    # Build clean output — drop heavy internal fields whisper adds
    segments = [
        {
            "id": seg["id"],
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
            "avg_logprob": round(seg.get("avg_logprob", 0), 4),
            "no_speech_prob": round(seg.get("no_speech_prob", 0), 4),
        }
        for seg in result["segments"]
    ]

    # Duration = end of last segment
    duration = segments[-1]["end"] if segments else 0.0

    transcript = {
        "youtube_id": youtube_id,
        "language": result.get("language", "en"),
        "duration_seconds": duration,
        "model_used": model_name,
        "segments": segments,
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(transcript, indent=2, ensure_ascii=False))

    print(f"[transcriber] Saved {len(segments)} segments → {out}")
    print(f"[transcriber] Duration: {duration/60:.1f} min | Language: {transcript['language']}")

    return transcript


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    transcribe(model_name=model)
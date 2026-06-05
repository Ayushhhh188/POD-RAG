"""
downloader.py
Downloads audio from a YouTube URL using yt-dlp.
Output: data/audio.mp3
"""

import subprocess
import sys
from pathlib import Path


def download_audio(youtube_url: str, output_path: str = "data/audio.mp3") -> Path:
    """
    Downloads audio-only stream from a YouTube URL and saves as mp3.

    Args:
        youtube_url: https://youtu.be/Rni7Fz7208c?si=gNv8s4KVoQrwDdAs
        output_path: Relative path for the output file (default: data/audio.mp3)

    Returns:
        Path to the downloaded mp3 file.

    Raises:
        RuntimeError: If yt-dlp exits with a non-zero return code.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # yt-dlp writes to data/audio.mp3 directly via the template
    # %(ext)s is replaced by "mp3" after post-processing
    template = str(output.with_suffix(".%(ext)s"))

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",          # best quality
        "--output", template,
        "--no-playlist",
        "--no-check-certificates",       # handles self-signed cert envs
        "--js-runtimes", "nodejs",       # use Node.js for YouTube JS extraction
        "--extractor-args", "youtube:player_client=android,web", # fallback clients
        youtube_url,
    ]

    print(f"[downloader] Starting download: {youtube_url}")
    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed with exit code {result.returncode}. "
            "Make sure yt-dlp is installed and the URL is valid."
        )

    if not output.exists():
        raise FileNotFoundError(
            f"Download appeared to succeed but {output} was not found. "
            "Check yt-dlp output above for clues."
        )

    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"[downloader] Done — {output} ({size_mb:.1f} MB)")
    return output


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://youtu.be/Rni7Fz7208c?si=gNv8s4KVoQrwDdAs"
    download_audio(url)
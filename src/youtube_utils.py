"""
youtube_utils.py
Utility functions for converting timestamps and building YouTube deep-links.

These are pure functions with no dependencies — safe to import anywhere.
"""


def seconds_to_timestamp(seconds: float) -> str:
    """
    Convert float seconds to a human-readable MM:SS or HH:MM:SS string.

    Examples:
        75.4  → "1:15"
        3661  → "1:01:01"
    """
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def seconds_to_youtube_url(youtube_id: str, start_sec: float) -> str:
    """
    Build a YouTube deep-link URL that begins playback at start_sec.

    Args:
        youtube_id: The 11-character YouTube video ID (e.g. "Rni7Fz7208c")
        start_sec:  Start time in seconds (floats are floored to int)

    Returns:
        URL string, e.g. "https://www.youtube.com/watch?v=Rni7Fz7208c&t=75s"
    """
    return f"https://www.youtube.com/watch?v={youtube_id}&t={int(start_sec)}s"


def seconds_to_embed_url(youtube_id: str, start_sec: float) -> str:
    """
    Build a YouTube embed URL (for iframes) with autoplay at start_sec.

    Args:
        youtube_id: The 11-character YouTube video ID
        start_sec:  Start time in seconds

    Returns:
        Embed URL string for use in <iframe src="...">
    """
    return (
        f"https://www.youtube.com/embed/{youtube_id}"
        f"?start={int(start_sec)}&autoplay=1"
    )


def format_source_label(start_sec: float, end_sec: float) -> str:
    """
    Returns a human-readable source label for a chunk.

    Example: "1:15 – 2:00"
    """
    return f"{seconds_to_timestamp(start_sec)} – {seconds_to_timestamp(end_sec)}"


if __name__ == "__main__":
    # Quick sanity checks
    assert seconds_to_timestamp(0)     == "0:00"
    assert seconds_to_timestamp(75)    == "1:15"
    assert seconds_to_timestamp(3661)  == "1:01:01"
    assert "t=75s" in seconds_to_youtube_url("abc123", 75.4)
    assert "start=75" in seconds_to_embed_url("abc123", 75.4)
    print("youtube_utils: all checks passed")
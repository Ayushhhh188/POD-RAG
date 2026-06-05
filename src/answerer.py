"""
answerer.py
Takes a user query + retrieved chunks and calls Gemini 2.5 Flash to produce:
  - A grounded answer based only on the podcast transcript
  - The single best timestamp to jump to in the video
  - The source chunks used (for citation display in the UI)

Design decisions:
  - Gemini 2.5 Flash: fast, cheap, 1M context — perfect for RAG
  - Structured JSON response: easier to parse than free-form text
  - Grounded strictly to transcript: bot won't hallucinate beyond what was said
  - If the answer isn't in the transcript, it says so honestly
"""
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)
import json
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.retriever import retrieve, format_context
from src.youtube_utils import seconds_to_youtube_url, seconds_to_timestamp, format_source_label

load_dotenv()

GEMINI_MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = """
You are a podcast assistant.

Your task is to answer the user's question using ONLY the transcript excerpts provided.

Rules:

* Use only information present in the transcript excerpts.
* Do not use outside knowledge.
* Be conversational, clear, and concise.
* Write the answer as a short paragraph (2–5 sentences).
* If the answer is not present in the transcript, say that clearly.
* Do not quote large portions of the transcript verbatim.
* Summarize naturally in your own words.

Return ONLY valid JSON in exactly this format:

{
"answer": "A clear natural-language answer to the user's question.",
"confidence": "high",
"not_found": false
}

If the answer is only partially covered:
{
"answer": "...",
"confidence": "medium",
"not_found": false
}

If the answer is not found:
{
"answer": "The transcript excerpts do not contain enough information to answer this question.",
"confidence": "low",
"not_found": true
}
"""



def get_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise EnvironmentError(
            "GOOGLE_API_KEY not found.\n"
            "Add it to your .env file:\n"
            "  GOOGLE_API_KEY=your_key_here"
        )
    return key


def ask(
    query:         str,
    top_k:         int = 5,
    index_path:    str = "data/faiss_index.bin",
    metadata_path: str = "data/chunk_metadata.pkl",
) -> dict:
    """
    Full RAG pipeline: retrieve → prompt → generate → parse.

    Args:
        query:         The user's question
        top_k:         Number of chunks to retrieve (default 5)
        index_path:    Path to FAISS index
        metadata_path: Path to chunk metadata

    Returns:
        {
            "answer":       str,   — the answer text
            "timestamp_sec": float, — best timestamp in seconds
            "timestamp_fmt": str,  — human-readable e.g. "4:30"
            "youtube_url":  str,   — deep-link to that moment
            "confidence":   str,   — "high" | "medium" | "low"
            "not_found":    bool,  — True if answer not in transcript
            "sources":      list,  — the retrieved chunks (for UI display)
        }
    """
    # ── Step 1: Retrieve relevant chunks ─────────────────────────────────────
    chunks = retrieve(query, top_k=top_k, index_path=index_path, metadata_path=metadata_path)

    print("\n===== RETRIEVED CHUNKS =====")
    for i, c in enumerate(chunks):
        print(f"\nChunk {i}")
        print(c["text"][:500])
    print("===========================\n")

    if not chunks:
        return {
            "answer":        "I couldn't find any relevant sections in the transcript.",
            "timestamp_sec": 0.0,
            "timestamp_fmt": "0:00",
            "youtube_url":   "",
            "confidence":    "low",
            "not_found":     True,
            "sources":       [],
        }

    # ── Step 2: Build prompt ──────────────────────────────────────────────────
    context = format_context(chunks)

    user_message = f"""Transcript excerpts:

{context}

---

Question: {query}"""

    # ── Step 3: Call Gemini 2.5 Flash ─────────────────────────────────────────
    client = genai.Client(
        api_key=get_api_key()
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=2048,
            response_mime_type="application/json",
        ),
    )

    print("\n===== FULL RESPONSE =====")
    print(response)

    print("\n===== RAW RESPONSE =====")
    print(repr(response.text))
    print("========================\n")

    raw_text = response.text.strip()

    # ── Step 4: Parse response (handle double-wrapped JSON) ───────────────────
    parsed = json.loads(raw_text)
    print(type(parsed))

    # If Gemini returns a JSON string wrapped inside another JSON string,
    # parse the inner string to get the actual dict.
    if isinstance(parsed, str):
        parsed = json.loads(parsed)
        print("Double-wrapped JSON detected — parsed inner string.")

    print("\n===== PARSED =====")
    print(type(parsed))
    print(parsed)
    print(parsed["answer"])
    print("==================\n")

    # ── Step 5: Resolve best timestamp ───────────────────────────────────────
    timestamp_sec = chunks[0]["start_sec"]
    youtube_id    = chunks[0].get("youtube_id", "Rni7Fz7208c")

    return {
        "answer": parsed["answer"],
        "timestamp_sec": timestamp_sec,
        "timestamp_fmt": seconds_to_timestamp(timestamp_sec),
        "youtube_url": seconds_to_youtube_url(youtube_id, timestamp_sec),
        "confidence": parsed.get("confidence", "medium"),
        "not_found": parsed.get("not_found", False),
        "sources": chunks,
    }


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "What does Elon say about first principles thinking?"

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    result = ask(query)

    print(f"Answer ({result['confidence']} confidence):")
    print(f"  {result['answer']}\n")
    print(f"Best timestamp: {result['timestamp_fmt']}")
    print(f"Watch here:     {result['youtube_url']}\n")
    print(f"Sources used:")
    for s in result["sources"]:
        print(f"  [{format_source_label(s['start_sec'], s['end_sec'])}] score={s['score']} — {s['text'][:80]}...")
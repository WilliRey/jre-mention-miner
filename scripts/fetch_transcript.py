#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)


EPISODES_DIR = Path(__file__).resolve().parents[1] / "public" / "episodes"


def choose_english_transcript(transcripts) -> Any:
    """Pick the best available English transcript.

    Preference order:
    1) Manually created English transcript
    2) Auto-generated English transcript
    3) First available transcript
    """
    manual_en = None
    auto_en = None

    for t in transcripts:
        lang = (t.language_code or "").lower()
        is_en = lang == "en" or lang.startswith("en-")
        if is_en and not t.is_generated:
            manual_en = t
            break
        if is_en and auto_en is None:
            auto_en = t

    return manual_en or auto_en or (transcripts[0] if transcripts else None)


def fetch_transcript_once(video_id: str) -> List[Dict[str, Any]]:
    """Fetch a transcript once, without retry logic."""
    try:
        # Try direct English transcript first
        return YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    except (TranscriptsDisabled, NoTranscriptFound):
        # Fall back to listing transcripts and picking best match
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except TranscriptsDisabled:
            raise
        except NoTranscriptFound:
            raise
        except Exception as e:  # noqa: BLE001
            raise CouldNotRetrieveTranscript(str(e)) from e

        chosen = choose_english_transcript(list(transcript_list))
        if not chosen:
            raise NoTranscriptFound(f"No usable transcript for {video_id}")

        return chosen.fetch()


def fetch_transcript(video_id: str, max_retries: int = 3, backoff_seconds: int = 5) -> int:
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)

    # If a raw transcript already exists, don't refetch every run
    out_path = EPISODES_DIR / f"{video_id}.json"
    if out_path.exists():
        print(f"Transcript already exists for {video_id} at {out_path}")
        return 0

    attempt = 0
    while True:
        attempt += 1
        try:
            transcript = fetch_transcript_once(video_id)
            break
        except TranscriptsDisabled:
            print(f"Transcripts disabled for {video_id}", file=sys.stderr)
            return 1
        except NoTranscriptFound:
            print(f"No transcript found for {video_id}", file=sys.stderr)
            return 1
        except CouldNotRetrieveTranscript as e:
            # Network / 429 / transient issues
            if attempt >= max_retries:
                print(
                    f"Failed to retrieve transcript for {video_id} after {attempt} attempts: {e}",
                    file=sys.stderr,
                )
                return 1
            wait_for = backoff_seconds * attempt
            print(
                f"Transient error fetching transcript for {video_id} (attempt {attempt}/{max_retries}): {e}. "
                f"Retrying in {wait_for}s...",
                file=sys.stderr,
            )
            time.sleep(wait_for)
        except Exception as e:  # noqa: BLE001
            print(f"Unexpected error fetching transcript for {video_id}: {e}", file=sys.stderr)
            return 1

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)

    print(str(out_path))
    return 0


def main(argv):
    if len(argv) != 2:
        print("Usage: fetch_transcript.py <video_id>", file=sys.stderr)
        return 1
    video_id = argv[1]
    return fetch_transcript(video_id)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

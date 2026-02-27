#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


EPISODES_DIR = Path(__file__).resolve().parents[1] / "public" / "episodes"


def fetch_transcript(video_id: str):
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    except TranscriptsDisabled:
        print(f"Transcripts disabled for {video_id}", file=sys.stderr)
        return 1
    except NoTranscriptFound:
        print(f"No transcript found for {video_id}", file=sys.stderr)
        return 1

    out_path = EPISODES_DIR / f"{video_id}.json"
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

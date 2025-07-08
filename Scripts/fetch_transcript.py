#!/usr/bin/env python
import json, pathlib, sys
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

def fetch(vid):
    try:
        return YouTubeTranscriptApi.get_transcript(vid, languages=["en"])
    except NoTranscriptFound as e:
        print(f"No captions for {vid}: {e}")
        return []

if __name__ == "__main__":
    vid = sys.argv[1]                     # e.g. DKUCkIkB4Zw
    data = fetch(vid)
    out = pathlib.Path(f"public/episodes/{vid}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, out.open("w"), indent=2)
    print(f"Wrote {out} ({len(data)} lines)")

#!/usr/bin/env python3
"""Run fetch + parse for all IDs in config/video_ids.txt.

Usage:
  python scripts/run_all.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "video_ids.txt"


def iter_ids():
  if not CONFIG.exists():
    print(f"Config file not found: {CONFIG}", file=sys.stderr)
    return []
  ids = []
  for line in CONFIG.read_text(encoding="utf-8").splitlines():
    line = line.split("#", 1)[0].strip()
    if not line:
      continue
    ids.append(line)
  return ids


def run():
  ids = iter_ids()
  if not ids:
    print("No IDs found in config/video_ids.txt")
    return 1

  for vid in ids:
    print(f"=== Processing {vid} ===")
    for script in ("fetch_transcript.py", "parse_mentions.py"):
      cmd = [sys.executable, str(ROOT / "scripts" / script), vid]
      print(" ", " ".join(cmd))
      result = subprocess.run(cmd, cwd=ROOT)
      if result.returncode != 0 and script == "fetch_transcript.py":
        print(f"[WARN] fetch_transcript failed for {vid}, skipping parse", file=sys.stderr)
        break

  return 0


if __name__ == "__main__":
  raise SystemExit(run())

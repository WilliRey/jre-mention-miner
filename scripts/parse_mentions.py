#!/usr/bin/env python3
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Tuple

import spacy


ROOT = Path(__file__).resolve().parents[1]
EPISODES_DIR = ROOT / "public" / "episodes"
PARSED_SUFFIX = "-parsed.json"


# Brands and products to always skip
SKIP_BRANDS = {
    # Common JRE sponsors / ad reads
    "BetterHelp",
    "DraftKings",
    "Cash App",
    "Onnit",
    "Athletic Greens",
    "AG1",
    "ExpressVPN",
    "MeUndies",
    "Squarespace",
    "Blue Apron",
    "Eight Sleep",
    "Whoop",
    "Manscaped",
    "Liquid IV",
    "DoorDash",
    "Postmates",
    "LegalZoom",
    "ZipRecruiter",
    "Honey",
    "Rocket Mortgage",
    "Keeps",
    "Roman",
    # Household legacy brands
    "Coca-Cola",
    "Coke",
    "Pepsi",
    "Gatorade",
    "Nike",
    "Adidas",
    "McDonald's",
    "Starbucks",
    "Amazon",
}


AD_PHRASES = [
    "this episode is brought to you by",
    "this podcast is brought to you by",
    "sponsor of the show",
    "sponsors of the show",
    "our sponsor today",
    "our sponsors today",
    "promo code",
    "use code",
    "dot com slash",
    ".com slash",
    "enter code",
]


NICOTINE_PATTERN = re.compile(
    r"\b(zyn|nicotine|pouch(?:es)?|snus|vape|vaping|e-?cig(?:arette)?s?)\b",
    re.IGNORECASE,
)


MEDIA_PATTERNS = [
    (re.compile(r"jamie,? pull (that|it) up", re.IGNORECASE), "video"),
    (re.compile(r"pull (that|it) up", re.IGNORECASE), "video"),
    (re.compile(r"can you pull .* up", re.IGNORECASE), "video"),
    (re.compile(r"play (that|it|this)", re.IGNORECASE), "video"),
    (re.compile(r"roll the clip", re.IGNORECASE), "video"),
    (re.compile(r"let's watch", re.IGNORECASE), "video"),
    (re.compile(r"watch this", re.IGNORECASE), "video"),
    (re.compile(r"play the song|play some music", re.IGNORECASE), "song"),
    (re.compile(r"listen to this", re.IGNORECASE), "audio"),
]


CATEGORY_KEYWORDS = {
    "nicotine": ["zyn", "nicotine", "pouch", "pouches", "snus", "vape", "vaping"],
    "supplement": ["supplement", "vitamin", "powder", "capsule", "pill"],
    "software": ["app", "software", "platform", "website"],
    "book": ["book", "author", "novel"],
}


def load_nlp():
    try:
        return spacy.load("en_core_web_lg")
    except OSError:
        # Fallback to small model if large is unavailable
        return spacy.load("en_core_web_sm")


def is_ad_block(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in AD_PHRASES)


def guess_categories(name: str, context: str) -> List[str]:
    text = f"{name} {context}".lower()
    tags: List[str] = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            tags.append(cat)
    # Nicotine gets explicit age/regulatory tag
    if NICOTINE_PATTERN.search(text):
        if "nicotine" not in tags:
            tags.append("nicotine")
        tags.append("age/regulatory")
    return sorted(set(tags))


def score_product(name: str, context: str, in_ad_block: bool) -> float:
    """Heuristic confidence score (0–1).

    Factors:
    - Penalize mentions inside clear ad blocks.
    - Boost if looks niche (not all caps, length > 3, etc.).
    - Light boost if nicotine-related.
    """
    base = 0.7

    # Ad blocks are more likely to be sponsor reads
    if in_ad_block:
        base -= 0.3

    simple = name.strip()
    if len(simple) <= 3:
        base -= 0.1
    if simple.isupper():
        base -= 0.1

    text = f"{name} {context}".lower()
    if NICOTINE_PATTERN.search(text):
        base += 0.15

    # Clamp to [0, 1]
    return max(0.0, min(1.0, base))


def bucket_key(name: str, t: float) -> Tuple[str, int]:
    """Key for deduping: normalize name, bucket timestamp by 30s window."""
    norm = name.strip().lower()
    bucket = int(math.floor(t / 30.0))  # 30-second buckets
    return norm, bucket


def process_episode(nlp, video_id: str):
    raw_path = EPISODES_DIR / f"{video_id}.json"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw transcript not found: {raw_path}")

    with raw_path.open("r", encoding="utf-8") as f:
        segments = json.load(f)

    # Collect raw hits first
    raw_products: List[Dict[str, Any]] = []
    media: List[Dict[str, Any]] = []

    skip_until_idx = -1

    for idx, seg in enumerate(segments):
        text = seg.get("text", "")
        start = float(seg.get("start", 0))

        if not text:
            continue

        # Detect ad block start
        if is_ad_block(text):
            skip_until_idx = max(skip_until_idx, idx + 15)  # skip next ~15 lines

        in_ad_block = idx <= skip_until_idx

        # Media cues (always captured, even in ad reads)
        for pattern, mtype in MEDIA_PATTERNS:
            if pattern.search(text):
                media.append({
                    "t": start,
                    "cue": text.strip(),
                    "type": mtype,
                })
                break

        # Run NER
        doc = nlp(text)

        for ent in doc.ents:
            if ent.label_ not in {"ORG", "PRODUCT"}:
                continue

            name = ent.text.strip()
            if name.lower() in (b.lower() for b in SKIP_BRANDS):
                # Always skip explicit SKIP brands
                continue

            context = text.strip()
            tags = guess_categories(name, context)
            confidence = score_product(name, context, in_ad_block)

            raw_products.append({
                "t": start,
                "name": name,
                "context": context,
                "tags": tags,
                "confidence": confidence,
            })

        # Nicotine mentions that might not be captured as entities
        if NICOTINE_PATTERN.search(text):
            raw_products.append({
                "t": start,
                "name": "Nicotine product",
                "context": text.strip(),
                "tags": ["nicotine", "age/regulatory"],
                "confidence": 0.9,
            })

    # Dedupe: bucket by normalized name + 30s window, keep highest-confidence hit
    buckets: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for hit in raw_products:
        key = bucket_key(hit["name"], hit["t"])
        existing = buckets.get(key)
        if existing is None or hit["confidence"] > existing["confidence"]:
            buckets[key] = hit

    products = sorted(buckets.values(), key=lambda h: h["t"])

    out = {
        "episode_id": video_id,
        "products": products,
        "media": media,
    }

    out_path = EPISODES_DIR / f"{video_id}{PARSED_SUFFIX}"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(str(out_path))


def main(argv):
    if len(argv) != 2:
        print("Usage: parse_mentions.py <video_id>", file=sys.stderr)
        return 1

    video_id = argv[1]
    nlp = load_nlp()
    process_episode(nlp, video_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

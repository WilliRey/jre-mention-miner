#!/usr/bin/env python
import sys, json, re, pathlib, spacy, itertools
nlp = spacy.load("en_core_web_lg")
VIDEO_RE = re.compile(r"(pull|play|look).*?(video|clip|song)", re.I)
SKIP = { "coca-cola", "gatorade", "betterhelp", "draftkings" }

def parse(transcript):
    products, media = [], []
    for item in transcript:
        ts = item.get("start")
        text = item["text"]
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in {"ORG","PRODUCT"} and ent.text.lower() not in SKIP:
                products.append({"t": ts, "name": ent.text, "context": text})
        if VIDEO_RE.search(text):
            media.append({"t": ts, "cue": text})
    return {"products": products, "media": media}

def main():
    vid = sys.argv[1]
    raw = json.load(open(f"public/episodes/{vid}.json"))
    parsed = parse(raw)
    out = pathlib.Path(f"public/episodes/{vid}-parsed.json")
    json.dump(parsed, out.open("w"), indent=2)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()

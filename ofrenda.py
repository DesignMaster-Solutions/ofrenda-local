#!/usr/bin/env python3
"""Ofrenda Local: turn a recorded family story into an ofrenda card, fully offline.

audio -> whisper.cpp (local) -> Gemma (open weights, llama.cpp server) -> ofrenda.html + story.md
"""
import argparse
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request

LLM_URL = os.environ.get("OFRENDA_LLM", "http://127.0.0.1:18099/v1/chat/completions")
WHISPER_MODEL = os.environ.get("OFRENDA_WHISPER", os.path.expanduser("~/.cache/whisper-models/ggml-small.bin"))

# Grammar-constrained output: llama.cpp turns this schema into a GBNF grammar, so a 1B model
# cannot return anything but this shape.
SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "relation": {"type": "string"},
        "foods": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "songs": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "places": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "sayings": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "remembrance": {"type": "string", "minLength": 120, "maxLength": 600},
    },
    "required": ["name", "relation", "foods", "songs", "places", "sayings", "remembrance"],
}

PROMPT = """You are helping a family build an ofrenda for Día de los Muertos.
Below is a transcript of a relative telling a story about someone who passed away.
Extract ONLY what is said in the transcript: the person's name, how they relate to the speaker,
their favorite foods, songs or singers, places, and things they used to say
(quote each saying whole, exactly as spoken, even when the transcript breaks it with periods).
Never invent details that are not in the transcript; leave a list empty if nothing was said.
Then write "remembrance": 3 warm sentences in the speaker's voice, using only facts from the transcript.
No opinions or judgments about the person's choices; just remember them.

Transcript:
\"\"\"{transcript}\"\"\""""


def pauses(wav: pathlib.Path) -> list[float]:
    """Midpoints of silences longer than 0.2 s (where a speaker usually switches language)."""
    log = subprocess.run(["ffmpeg", "-i", str(wav), "-af", "silencedetect=noise=-35dB:d=0.2", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return [(s + e) / 2 for s, e in zip(starts, ends)]


def transcribe(audio: pathlib.Path) -> str:
    """Whisper picks ONE language per file and drops the rest, so bilingual stories lose the quotes.
    Cut at pauses and let whisper detect the language of each phrase."""
    with tempfile.TemporaryDirectory() as tmp:
        wav = pathlib.Path(tmp) / "all.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio), "-ar", "16000", "-ac", "1", str(wav)], check=True)
        cuts = [0.0] + pauses(wav) + [None]
        text = []
        for i, (a, b) in enumerate(zip(cuts, cuts[1:])):
            part = pathlib.Path(tmp) / f"p{i}.wav"
            span = ["-ss", str(a)] + (["-to", str(b)] if b else [])
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), *span, str(part)], check=True)
            # the story so far is the prompt, so short phrases keep names and places spelled consistently
            ctx = ["--prompt", " ".join(text)[-400:]] if text else []
            out = subprocess.run(["whisper-cli", "-m", WHISPER_MODEL, "-f", str(part), "-nt", "-np", "-l", "auto", *ctx],
                                 check=True, capture_output=True, text=True).stdout
            text.append(" ".join(out.split()))
        return " ".join(t for t in text if t)


def extract(transcript: str) -> dict:
    body = {
        "messages": [{"role": "user", "content": PROMPT.format(transcript=transcript)}],
        "temperature": 0.2,
        "response_format": {"type": "json_schema", "json_schema": {"name": "ofrenda", "schema": SCHEMA}},
    }
    req = urllib.request.Request(LLM_URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.load(r)
    card = json.loads(data["choices"][0]["message"]["content"])
    card["remembrance"] = three_sentences(card["remembrance"])
    card["model"] = data.get("model", "local")
    return card


def three_sentences(text: str) -> str:
    """Small models sometimes keep writing (or echo the prompt) until maxLength: keep the 3 sentences we asked for."""
    sentences = re.findall(r"[^.!?]+[.!?]+[\"'”’]*", text.replace("*", ""))
    return " ".join(x.strip() for x in sentences[:3]) or text


def grounded(card: dict, transcript: str) -> dict:
    """Drop list items the model could not have heard: every kept item must share a word with the transcript."""
    words = {w.strip(".,!?\"'").lower() for w in transcript.split()}
    for key in ("foods", "songs", "places", "sayings"):
        card[key] = [i for i in card[key] if {w.strip(".,!?\"'").lower() for w in i.split()} & words]
    return card


def li(items):
    return "".join(f"<li>{html.escape(i)}</li>" for i in items) or "<li class=empty>(not mentioned)</li>"


def render(card: dict, transcript: str) -> str:
    e = html.escape
    return f"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Ofrenda for {e(card['name'])}</title>
<style>
body{{margin:0;background:#1b0f24;color:#fdf3e1;font:17px/1.55 Georgia,serif}}
main{{max-width:760px;margin:auto;padding:40px 20px}}
h1{{font-size:2.3rem;margin:0;color:#ffb13b;text-align:center}}
.rel{{text-align:center;opacity:.8;margin-bottom:28px}}
.candles{{text-align:center;font-size:1.6rem;letter-spacing:.6em}}
.candles span{{display:inline-block;animation:flick 2.4s infinite alternate}}
.candles span:nth-child(2){{animation-delay:.7s}}.candles span:nth-child(3){{animation-delay:1.3s}}
@keyframes flick{{from{{opacity:.55;transform:scale(.94)}}to{{opacity:1;transform:scale(1.04)}}}}
@media (prefers-reduced-motion:reduce){{.candles span{{animation:none}}}}
blockquote{{border-left:4px solid #e2552c;margin:24px 0;padding:6px 18px;font-style:italic}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
section{{background:#2a1736;border:1px solid #5b2f4c;border-radius:10px;padding:14px 18px}}
h2{{font-size:1rem;margin:0 0 6px;color:#ffb13b;text-transform:uppercase;letter-spacing:.08em}}
ul{{margin:0;padding-left:18px}}.empty{{opacity:.5}}
details{{margin-top:28px;opacity:.85}}footer{{margin-top:28px;font-size:.8rem;opacity:.6;text-align:center}}
</style><main>
<div class=candles aria-hidden=true><span>🕯️</span><span>🌼</span><span>🕯️</span></div>
<h1>{e(card['name'])}</h1><p class=rel>{e(card['relation'])}</p>
<blockquote>{e(card['remembrance'])}</blockquote>
<div class=grid>
<section><h2>Favorite foods</h2><ul>{li(card['foods'])}</ul></section>
<section><h2>Songs &amp; singers</h2><ul>{li(card['songs'])}</ul></section>
<section><h2>Places</h2><ul>{li(card['places'])}</ul></section>
<section><h2>Things they used to say</h2><ul>{li(card['sayings'])}</ul></section>
</div>
<details><summary>Full transcript</summary><p>{e(transcript)}</p></details>
<footer>Made offline with whisper.cpp and {e(card['model'])} on this computer. Nothing left the machine.</footer>
</main></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("audio", type=pathlib.Path, help="recorded story (any format ffmpeg reads)")
    ap.add_argument("-t", "--transcript", type=pathlib.Path,
                    help="use this (hand-corrected) transcript instead of transcribing again")
    ap.add_argument("-o", "--out", type=pathlib.Path, default=pathlib.Path("out"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    transcript = a.transcript.read_text().strip() if a.transcript else transcribe(a.audio)
    if len(transcript.split()) < 12:
        sys.exit("transcript is empty or too short: nothing to remember, refusing to let the model invent a person")
    (a.out / "transcript.txt").write_text(transcript + "\n")
    print("transcript:", transcript, file=sys.stderr)
    card = grounded(extract(transcript), transcript)
    if not grounded({"foods": [card["name"]], "songs": [], "places": [], "sayings": []}, transcript)["foods"]:
        sys.exit(f"model named someone who is not in the story ({card['name']!r}); fix the transcript and retry")
    (a.out / "ofrenda.json").write_text(json.dumps(card, ensure_ascii=False, indent=2))
    (a.out / "story.md").write_text(f"# {card['name']}\n\n{card['remembrance']}\n\n## Transcript\n\n{transcript}\n")
    (a.out / "ofrenda.html").write_text(render(card, transcript))
    print(json.dumps(card, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

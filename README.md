# Ofrenda Local

Record a relative telling a story about someone who passed away. Ofrenda Local turns that recording into an
ofrenda card (favorite foods, songs, places, the things they used to say, and a short remembrance) **without
anything leaving your computer**.

Built for the DEV Hacktoberfest Open-Source AI Challenge, week 4: *Ghost in the Machine*.

```
story.m4a ──ffmpeg──► 16 kHz wav ──silence cuts──► phrases ──whisper.cpp (language per phrase)──► transcript
transcript ──Gemma 3 4B on llama.cpp (JSON-schema grammar)──► card ──grounding filter──► ofrenda.html + story.md
```

## Run it

```bash
brew install llama.cpp whisper-cpp ffmpeg
# whisper model: ggml-small.bin from https://huggingface.co/ggerganov/whisper.cpp
llama-server -hf ggml-org/gemma-3-4b-it-GGUF --port 18099 -c 4096 &
python3 ofrenda.py samples/abuela-rosa.m4a -o out          # transcribe + build the card
python3 ofrenda.py samples/abuela-rosa.m4a -t out/transcript.txt -o out   # after fixing names by hand
open out/ofrenda.html
```

Env vars: `OFRENDA_LLM` (any OpenAI-compatible endpoint that supports `json_schema`), `OFRENDA_WHISPER` (model path).
Python standard library only. Tests: `python3 -m unittest discover -s test`.

## Choices that matter

- **Language per phrase.** Whisper detects one language per file. Grandparents switch languages mid-sentence,
  and the Spanish sayings were the first thing whisper dropped. The audio is cut at pauses and each phrase is
  transcribed with its own language detection, with the story so far as the prompt so names stay consistent.
- **Grammar-constrained output.** llama.cpp compiles the JSON schema into a grammar, so even a small model can only
  answer in the card's shape (and the remembrance has a minimum length).
- **No invented relatives.** Every list item must share words with the transcript or it is dropped; an empty or
  near-empty transcript is refused, and so is a card whose name is not in the story. Without these checks the model
  happily wrote a full remembrance for an "Abuelo Ricardo" that nobody mentioned.
- **The family corrects, the model doesn't guess.** `transcript.txt` is saved next to the card; fix "tamales de rojas"
  to "rajas" and run again with `-t`.

## Sample

`samples/abuela-rosa.m4a` is a **synthetic** recording made with the macOS `say` voices (Samantha for English,
Paulina for the Spanish sayings) from `samples/abuela-rosa.txt`; Rosa Delgado is a fictional grandmother.
`samples/abuela-rosa.corrected.txt` is the whisper output with the four words a family member would fix.
The generated card is in [`docs/`](docs/) and live at https://designmaster-solutions.github.io/ofrenda-local/

License: MIT.

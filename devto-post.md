---
title: Ofrenda Local: my grandmother's sayings survived the transcript only after I stopped trusting one language per file
published: true
tags: devchallenge, hf26challenge, ai, opensource
cover_image: https://raw.githubusercontent.com/DesignMaster-Solutions/ofrenda-local/main/docs/cover.png
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)*

## What I Built

Ofrenda Local takes a voice recording of someone telling a story about a relative who passed away and turns it into an ofrenda card: the foods they cooked, the songs they sang, the places they lived, the exact things they used to say, and a short remembrance written in the speaker's voice. It also saves the transcript and a `story.md`, so the story is kept as text and not only as a pretty page.

Everything runs on the laptop. Transcription is whisper.cpp, the writing is Gemma 3 4B on llama.cpp, and the glue is one Python file with no dependencies outside the standard library.

I read the theme as "the memories and stories we carry with us". The ghost in this machine is the person in the recording. The machine should help keep them, and it must never put words in their mouth.

## Demo

Live card generated from the sample recording: https://designmaster-solutions.github.io/ofrenda-local/

The sample (`samples/abuela-rosa.m4a`) is synthetic: I wrote a short story about a fictional grandmother, Rosa Delgado, and voiced it with the macOS `say` voices, Samantha for the English and Paulina for her Spanish sayings. Full run on my Mac, from audio to HTML: about 16 seconds.

## Code

{% github DesignMaster-Solutions/ofrenda-local %}

## How I Built It

```
story.m4a -> ffmpeg -> 16 kHz wav -> cut at pauses -> whisper.cpp, language detected per phrase -> transcript
transcript -> Gemma 3 4B on llama-server, JSON schema compiled to a grammar -> card -> grounding filter -> ofrenda.html
```

Four things turned out to matter more than the model choice.

**1. Whisper picks one language per file.** My first transcript read: *"Whenever we complained, she used to say, And when we left her house she always said, I miss her hands..."*. Both Spanish sayings were gone. Whisper had detected English for the whole file and silently dropped the parts that were not English. Those sayings are the most important part of an ofrenda, and a family where grandma switches languages mid-sentence is the normal case, not the edge case.

The fix: run ffmpeg's `silencedetect` to find pauses, cut the audio there, and transcribe each phrase with `-l auto`. Now the sayings come through: *"Con paciencia y saliva, el elefante se comió a la hormiga."*

**2. Short phrases lose names.** Cutting fixed the language but broke the places: Oaxaca became "Wahaka" and Tlacolula became "Tulicalula", because a two-second clip has no context. whisper.cpp takes a `--prompt`, so each phrase now gets the last 400 characters of the story so far. Oaxaca and Tlacolula came back.

**3. Grammar beats begging.** With Gemma 3 1B the "remembrance" field came back as `":["`. Instead of a longer prompt, I gave llama-server a JSON schema (`response_format: json_schema`). llama.cpp compiles it into a grammar, so the model cannot produce anything but the card's shape, and `minLength: 120` on the remembrance means it cannot stop after two characters. I moved to Gemma 3 4B for the writing quality; the grammar is what made the output reliable.

**4. The model will invent a grandfather.** While testing I passed an empty transcript by mistake. Gemma returned a complete, touching remembrance for "Abuelo Ricardo", who loved pan dulce and La Bamba. Nobody had said a word. For a tool that writes about real people who died, that is the worst possible bug. So:

- an empty or very short transcript is refused before the model is called;
- every food, song, place and saying must share words with the transcript or it is dropped;
- if the card's name is not in the story, the run fails.

The same rule shaped the remembrance prompt. An early card ended with "It's a shame she moved from Oaxaca to San Antonio". Nobody said that either, so the prompt now asks for no opinions, and the code keeps only the three sentences it asked for, because a small model under a length constraint sometimes keeps going and starts echoing the prompt.

There are unit tests for the grounding filter and the HTML escaping, and I watched them fail with the filter disabled before trusting them.

Whisper still hears "tamales de rojas" instead of "rajas" and "Pedro in Fonte" instead of Pedro Infante. I did not try to make the model guess those. The transcript is saved next to the card, a family member fixes the four words, and `python3 ofrenda.py story.m4a -t out/transcript.txt` rebuilds the card from the corrected text. The family corrects, the model doesn't guess.

## Why Does Open Innovation Matter?

Because of what is in these recordings. A grandmother's voice, the names of everyone in the family, where they lived, the illness nobody talks about. That is not something I want to upload to a service so it can be turned into a card, and it is exactly the kind of recording families keep for fifty years. Running whisper.cpp and Gemma locally means the audio never leaves the machine, it works in a kitchen in Oaxaca with no internet, and it costs nothing per story.

Open also meant I could change the parts a closed API would not let me touch: transcribe per phrase with my own cut points, feed whisper its own running context, and constrain the model with a grammar instead of hoping it follows instructions. And in thirty years, when the services of today are gone, `llama-server` plus a GGUF file will still run the same story the same way.

## The Spirit of It

The last line of the sample is "I miss her hands, and her kitchen that always smelled like cinnamon." The card does not need to be clever. It needs to keep the champurrado, the Pedro Infante on the radio, and "Ve con Dios, mijo" exactly as she said it, and not add a single thing she didn't.

## Prize Categories

Best Use of Gemma: Gemma 3 4B (and 1B during development) runs locally through llama.cpp and writes every card, constrained by a JSON-schema grammar.

# Speech preservation: first live passes

11 September 2026. These tests use **synthetic Russian audio without a human-verified acoustic reference**. Results describe agreement with the supplied script, not measured accuracy on learner speech.

## Full-sentence synthesis

ElevenLabs `eleven_multilingual_v2` generated eight fixtures with one configured voice. Each was processed by MAI-Transcribe-2 in verbatim and clean modes, and OpenAI `gpt-transcribe` with a literal-transcription prompt.

| Intended sentence | MAI verbatim | MAI clean | OpenAI |
|---|---|---|---|
| Я хочу чай без **сахар**. | Returned **сахара** | Returned **сахара** | Returned **сахара** |
| Я звоню **сестра**. | Kept **сестра**, added a comma | Kept **сестра**, added a question mark | Kept **сестра** |
| Я вижу **красивый** кошку. | Returned **красивую** | Returned **красивую** | Returned **красивую** |
| Она каждый день **читаю** книгу. | Kept **читаю** | Kept **читаю** | Kept **читаю** |
| Мы завтра **идёт** в парк. | Kept **идёт** | Kept **идёт** | Kept **идет** |
| Можно чай без сахара? | Words unchanged | Words unchanged | Words unchanged |
| Без сахара, пожалуйста. | Words unchanged | Words unchanged | Words unchanged |
| Я хочу... нет, я хотел чай без сахара. | Repair retained | Repair retained | Repair retained |

Three of five deliberately wrong forms remained in every configuration. Two were replaced with the expected grammatical form. Synthesis may also change the intended sentence, so listening is required before attributing those replacements to recognition.

Punctuation also matters: `Я звоню, сестра` can address a sister rather than attempt a dative object. The assessor must consider that ambiguity. The comparison helper ignores punctuation, capitalisation and ё/е for lexical comparison, while raw output retains them.

Median recogniser request times: MAI verbatim **0.53 s**, MAI clean **0.54 s**, OpenAI **1.07 s**. These exclude synthesis, app upload, dialogue and response audio. MAI returned word timestamps; the OpenAI responses in this configuration did not.

## Independently spoken target segments

For the three case/agreement examples, the surrounding phrase and target word were synthesised separately and joined with short gaps. This reduces the synthesiser's opportunity to repair a whole sentence, but changes prosody and is still not a verified learner recording.

| Target | MAI verbatim | MAI clean | OpenAI |
|---|---|---|---|
| без **сахар** | Preserved | Preserved | Preserved |
| звоню **сестра** | Preserved | Preserved | Preserved |
| **красивый** кошку | Preserved | Preserved | Preserved |

All three forms remained across all configurations. The models can return incorrect forms; this does not establish reliable preservation in continuous speech or identify where the first pass changed. Both pauses and acoustic realisation changed between experiments.

## Text-coaching regression

`gpt-5.6-luna` on low reasoning received the intended text without audio, isolating grammar coaching from recognition. Version 1 identified the five deliberate errors but also suggested replacing the valid polite request `я хотел чай` and returned Russian explanations for English UI.

Version 2 accepts polite past-tense requests and repairs and explicitly selects English explanation fields. The rerun corrected all five deliberate errors, left both correct controls and self-repair unchanged, and returned English explanations. These results are conditional text feedback, not verification of spoken mistakes.

The final interface uses version 3, which removes repeated technical disclaimers from the generated prose while retaining the evidence label in the UI. A further genitive/self-repair/short-answer check passed; results are in `instance/conversation-e2e-20260911/coaching-v3.json`.

## Application-path comparison

The lab also processed the conjugation fixture through the actual app's 16 kHz WAV conversion. MAI verbatim and clean returned `Она каждый день читаю книгу.` OpenAI returned `А на каждый день читаю книгу.` The wrong verb remained, but the pronoun changed. This is a separate observation from the direct-MP3 harness; model variation and the different encoding path prevent attributing the discrepancy to one cause. The app retains both the original recording and every hypothesis. Its three-turn café test preserved `без сахар` in the transcript, offered `без сахара` separately, and remembered the tea/bun order when calculating 180 рублей.

## Local evidence

- `instance/speech-eval-20260911/`: full-sentence audio, original transcriptions/raw responses, first grammar pass.
- `instance/speech-eval-grammar-v2/`: rerun recognition and version-2 grammar feedback.
- `instance/speech-eval-segments-20260911/`: separate word segments, joined recordings and comparisons.
- `instance/conversation-e2e-20260911/`: synthetic café replies for browser testing.

Artifacts remain in ignored local runtime directories. See the [pilot guide](conversation-pilot.md) for reproducible commands and reference manifests. The next evidence should come from independently listened-to human recordings.

Microsoft documents verbatim fillers, false starts and repairs, without promising error-preserving Russian assessment. [Microsoft MAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe). The experiment uses OpenRouter's documented style and timestamp controls. [OpenRouter API guide](https://openrouter.ai/docs/guides/overview/multimodal/stt).

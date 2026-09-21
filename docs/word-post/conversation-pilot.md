# Conversation pilot

**Deprecated as a separate learner activity, 15 September 2026.** New conversations
now start in [Speaking](live-conversation.md) at `/#speaking`. The previous
recording-and-send game is retained as a saved-session viewer and as infrastructure
for Speech lab. Its data, audio and API compatibility remain intact. The description
below documents the original pilot; its old start/record controls are no longer
offered for learner conversations.

Implemented 11 September 2026: a usable speaking activity and a transcription-preservation experiment. Spoken-language grading is not yet calibrated.

## Try it

- `/#speaking`: start a live café conversation or open **Previous conversations** to replay older recordings, read optional English translations and revisit language notes. Saved recorded sessions use `/#speaking/recorded/<id>`; old session links still work.
- `/#speaking/lab`: under **Developer tools**, read a deliberately incorrect sentence or a correct control. Compare MAI verbatim, MAI clean and OpenAI on the same recording. The reference sentence is never sent to recognition.
- Current preview: `http://127.0.0.1:5052`.

## Models

| Work | Default |
|---|---|
| Recognition | `microsoft/mai-transcribe-2` through OpenRouter, verbatim with word timestamps |
| Lab comparisons | MAI clean; OpenAI `gpt-transcribe` with a literal-transcription prompt |
| Dialogue and separate text coaching | OpenAI `gpt-5.6-luna`, low reasoning |
| Character speech | Existing ElevenLabs model and voice pool |

Optional overrides: `CONVERSATION_TRANSCRIPTION_MODEL`, `CONVERSATION_COMPARISON_MODEL`, `CONVERSATION_MODEL`. Credentials use the existing dotenv loader: `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`. No secret `.env` file or preview settings were edited. Existing story/flashcard model choices were preserved.

A character's voice is chosen randomly from the configured pool at session creation and reused throughout that conversation. Existing card/story random voice selection is unchanged.

MAI requests explicitly set `provider.options.azure.enhancedMode.modelOptions.transcribeStyle`, `response_format: verbose_json` and `timestamp_granularities: [word]`. They do not rely on OpenRouter's ignored top-level transcription prompt. No provider is silently substituted. [OpenRouter speech API](https://openrouter.ai/docs/guides/overview/multimodal/stt), [MAI settings](https://openrouter.ai/microsoft/mai-transcribe-2). The comparator uses OpenAI's documented `gpt-transcribe` file endpoint; a literal prompt is not a guarantee of error preservation. [OpenAI transcription guide](https://developers.openai.com/api/docs/guides/speech-to-text).

## Storage and recovery

Migration `013_conversation.sql` adds `conversation_sessions` and `conversation_turns`. Sessions reference existing learner profiles and retain a scenario snapshot, chosen voice, UI language and start key. Turns retain order, upload fingerprint, duration, original audio reference, complete ASR response/model/settings/timestamps, comparisons, dialogue and separate coaching results.

Audio lives in `conversation-audio/` beside the configured SQLite database. Original bytes are retained. A temporary 16 kHz mono WAV is used for recognition without trimming silences. Private playback routes verify session ownership. Personal use follows the existing session and CSRF/origin protection; there is no new approval or PIN flow.

The local learning-store backup now includes referenced conversation audio with checksums. Restore `conversation-audio/` beside the restored database. Older backups can still contain recordings subsequently deleted from the live app.

The preview database was upgraded with an automatic pre-migration backup; its receipt is in ignored `instance/conversation-migration-20260911/migration.json`. Canonical database and configuration hashes were checked and unchanged.

Processing checkpoints each expensive result. Recognition happens first; dialogue and text coaching then run independently. Reply text can appear before its voice and notes finish. Retry reuses completed steps and the same turn. GET/poll never starts paid work. Two local jobs run concurrently; a durable five-minute lease permits explicit retry after a process restart. When the local worker pool is busy, the saved queued turn offers a retry control. A shared durable queue is still needed before running multiple hosted web processes.

Sessions allow eight turns. Browser recording stops after 60 seconds; the server accepts playable 0.2–90-second recordings up to 8 MB. Streaming WebM without a duration header is decoded to measure its duration. Microphone tracks stop on completion, errors and navigation, including a permission request resolving after unmount. File upload uses the same backend. CSP permits `blob:` only for local media previews.

## Assessment boundary

Coaching currently evaluates an **unverified transcript**, not audio. Its quoted source must actually occur in that text, and suggestions remain separate from the stored utterance. Explanations follow the interface language; Russian examples retain their original form.

There is no acoustic verifier, pronunciation/fluency grade, Elo change or coin award in this pilot. Stored scores remain null. Agreement between recognisers is not treated as proof. The first grammar test exposed an unnecessary correction of the valid café request `Я хотел чай`; coaching version 2 accepts that construction and successful self-repair.

Version 3 keeps those rules while shortening the learner-facing explanation; the evidence limitation appears once in the interface. A live check retained the genitive correction and accepted the polite self-repair and short valid reply without changes.

Version 4 additionally distinguishes an English-only reply from a Russian attempt
and redirects unrelated answers without inventing Russian errors. Transcripts and
audio remain untouched. Requests for a Russian phrase are treated as help-seeking;
transcripts with no Russian text cannot acquire Russian grammar corrections from
the model. Dialogue now shares `russian-cafe-v3` with the live activity:
the worker responds naturally that they do not understand English, then waits.
They do not translate an English request into a model Russian phrase. Help in
Russian and understandable Russian mistakes remain supported. English and mixed
Latin-script recognition results are omitted from the lesson display; raw evidence
and the diagnostic Speech lab remain unchanged. English translation of the worker's
reply remains a separate optional text field. Before a newly
generated recorded-turn reply reaches speech synthesis, the server checks for
Russian letters; a non-Russian or mixed Latin reply gets a short Russian recovery
message instead (`language_recovered` records this). This output check is never
used to reject a learner's names, mixed speech or grammatical mistakes. See the
[live language regression](live-conversation.md#language-regression-14-september-2026)
for the text/audio tests and their limitations. Models, voice selection,
credentials and historical sessions were not changed.

## Verification

229 Python tests and 76 UI tests pass, including 17 conversation/backend checks and 8 conversation UI checks. The production build and TypeScript check pass. Browser testing completed a three-turn order: tea, a bun and a price question; the agent remembered both items and returned 180 рублей. Original/reply audio supported private HTTP range playback, the saved session reopened, and the lab displayed all three transcripts. Browser microphone permission/cleanup is covered with simulated MediaRecorder tests; real-device microphone quality and human speech calibration remain to be tried.

## Reproduce the experiments

These commands make paid calls only with `--run`. Offline unit tests block external connections.

```bash
.venv/bin/python scripts/evaluate_speech.py \
  --output instance/my-speech-experiment --synthesise --run --assess

.venv/bin/python scripts/evaluate_speech.py \
  --output instance/my-segment-experiment --synthesise --segmented --run --limit 3

.venv/bin/python scripts/evaluate_speech.py \
  --manifest /absolute/path/references.json --output instance/human-speech-eval --run
```

A reference manifest contains objects with `id`, `text`, `audio` (absolute path), `source`, `reference_verified`, `target` and `correction`. Only set `reference_verified: true` after listening and checking the actual words. Synthetic runs always record false. Results preserve checksums, synthesis provenance, model/settings, raw outputs and timings. Reuse output directories only for identical fixtures/configuration; use a new directory when changing the model or corpus.

See [first experiment results](speech-preservation-results-20260911.md).

## Next work

1. Record and independently label human speech: wrong endings, valid colloquial constructions, repairs and unclear passages from several speakers.
2. Test an independent audio-aware verification pass, including apparently grammatical transcripts. Measure false corrections and uncertain/unscored cases.
3. Add measured audio timing/pause/repair features and validated rubrics; total recording length and provider latency are not fluency scores.
4. Link verified corrections to the existing lemma/form model and optional contextual clozes. Invalid spoken forms must remain representable even when absent from the valid-forms table.
5. Extend scenarios, hands-free interaction, server-authoritative rewards and hosted workers/storage after validating the core experience.

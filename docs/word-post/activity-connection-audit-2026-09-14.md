# Activity connection audit — 14 September 2026

The current OpenAI, OpenRouter and ElevenLabs credentials work. Real provider requests succeeded for every native activity tested below. No credentials or model selections were changed.

## Word Jumble incident

The preview logged `Sentence storage unavailable (OperationalError)` for the failed assessment at 19:12. This was an application database error, rather than a logged provider/authentication error. The old log did not include the SQLite code or message, so its precise cause cannot be established retrospectively.

The preview database passed SQLite integrity and foreign-key checks, and a write-lock probe succeeded. The assessment flow passed against a SQLite backup. Retrying the learner's unchanged answer in the browser then returned HTTP 200 and saved one assessment; the browser displayed the preserved answer and feedback.

Word Jumble now logs the SQLite code and message on storage failure, and the HTTP status/error class on provider failure. Provider response bodies and credentials are excluded. A regression test verifies rollback on a storage error, preservation of the previous draft, and a successful retry without duplicate assessments.

## Live checks

| Activity or dependency | Configured model | Result |
| --- | --- | --- |
| Word Jumble | `gpt-5-mini`, low | Assessment, persistence and browser feedback passed. |
| Translate a sentence | `gpt-5-mini`, low | Pair generation and checking an incorrect Russian conjugation passed. |
| Writing | `gpt-5-mini`, low | Initially rejected malformed generated vocabulary. After the fix, generation, page loading and assessment routes returned 200. |
| Read a story | `gpt-6-astra`, low; `gpt-5-mini` for checks | Bilingual titles/questions for a supplied passage, extra questions and answer assessment passed. |
| Lessons | `gpt-6-astra`, low | Preparation returned three objectives and six tasks; a separate answer assessment passed. |
| Native flashcards | `gpt-5.6-luna`, low | Generated and saved a genitive cloze using **чая**, linked to its lemma/form. |
| Flashcard pictures | `gpt-image-2` | Generated, stored and served a valid PNG through the app's asset route. |
| Speech | `eleven_multilingual_v2` | All four configured voices produced decodable audio. The flashcard's word and sentence audio also saved and served successfully. Random voice selection is preserved. |
| Recorded conversation | `gpt-5.6-luna`, low | Russian café reply and separate grammar feedback passed. |
| Primary transcription | `microsoft/mai-transcribe-2` via OpenRouter | Transcribed a generated Russian audio fixture successfully. |
| Comparison transcription | `gpt-transcribe` | Transcribed the same fixture successfully. |
| Live conversation | `gpt-live-1` | WebRTC audio exchange, Russian replies, graceful closure, saved recordings and background notes passed. |

The native activity pages and their options/library endpoints also returned 200. These are connection and representative workflow checks, not an exhaustive assessment of teaching quality or human speech recognition accuracy. The speech fixtures are synthetic. Test-created lessons, cards, recordings and exercise records stayed in an isolated database and asset folder; the learner's existing Word Jumble answer was the only assessment retried in the preview.

## Fixes made during the audit

- **Writing generation:** the model put a long list of alternatives inside one vocabulary item. The request now explicitly distinguishes the writing length from the vocabulary count, asks for one dictionary word per item, and gives the response schema the same text-length limits as local validation. Invalid output is still rejected rather than saved.
- **Story audio:** the service previously returned an audio URL even when ElevenLabs returned no file. It now returns a URL only when generation succeeds and the file exists. Regression coverage includes failed, missing-file and successful results.
- **Word Jumble diagnostics:** storage failures and provider failures now retain useful, distinct server-side diagnostics.

## Auxiliary connections

- **Yandex:** the configured key was rejected with HTTP 401. A valid Yandex Cloud credential is needed if this optional translation integration is retained. No current native activity depended on it during these tests; card generation uses contextual translations from its OpenAI generation call.
- **AnkiConnect:** no connection was available at the configured local endpoint. Anki and its AnkiConnect add-on must be running for export. Native flashcards are independent of it.
- **Google Drive:** outside this activity-provider pass; sync/authentication was not invoked.

The backend's separate generation, validation and persistence paths are working in the tested workflows, but error reporting remains uneven between older and newer services. A sensible next maintenance step is consistent safe provider diagnostics across activities, rather than changing keys or models to address local storage failures.

## Verification

95 regression tests passed across Word Jumble, Writing, Translation, provider integration, story titles, activity routes and Lessons. Changed Python modules compile and `git diff --check` passes. Credential files, preview settings and the canonical database were checked against pre-audit hashes and remained unchanged.

## Word Jumble follow-up: complete word sets and proportionate feedback

New rounds now keep matching library words and generate the missing entries to reach 3, 4 or 5 words for the selected difficulty. Live checks completed a two-word cinema set and generated sets for an empty topic at all three levels. The complete words stay with the activity; the canonical vocabulary ingestion flow is unchanged.

Tutor checks now use medium reasoning on the existing `gpt-5-mini` model; word selection remains low. Earlier low-reasoning trials still produced unnecessary rewrites and inaccurate grammar explanations. The revised prompt and final checks produced one concise spelling correction for `Я люблю сериалы и фильми`, accepted a correct sentence without a final full stop, corrected declension and conjugation examples, returned Russian feedback in the Russian interface, and accepted the longer creative rice sentence with only the missing-word point deducted. These representative checks do not establish error-free linguistic assessment.

27 service/route tests, 11 activity tests and 9 browser-script tests passed. The preview was restarted and the learner's film sentence checked once in the browser. Its earlier assessment remains in the collapsed history; all nine earlier checks were verified unchanged. The correction's accessibility text is now visually hidden correctly. Local evidence is under `instance/word-jumble-refinement-20260914/`; earlier unsuccessful trials and the final passing outputs are retained. Credential files, preview configuration and the canonical database were verified unchanged.

Detailed local test results, synthetic fixtures and the isolated test database are under `instance/activity-connection-audit-20260914/`. The preview runs at `http://127.0.0.1:5052`; the separate test server was stopped after verification.

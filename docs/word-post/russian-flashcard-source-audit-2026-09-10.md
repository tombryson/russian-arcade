# Russian flashcards: source audit and corrected migration requirements

10 September 2026. Audit of the Python generators, their pre-upgrade Git versions, the lexical schema/importers, native generation/review and the preview on port 5052. Findings and requirements, not an implemented migration. No provider generation, card edits, ratings, Anki writes or lexical migration were performed.

The native implementation has not preserved the central learning behaviour of the Anki workflow. The intended unit of practice is **a particular Russian form, in a sentence that uses its grammatical features correctly, with meaning, illustration and speech**. A lemma connects that material to the vocabulary; it does not replace practising its forms. Adding tags to lemma cards does not establish this behaviour.

The owner's requirements supersede the text-only MVP assumptions: automatic generation is the primary workflow; pictures and Russian recordings are essential to a completed generated card; case/conjugation practice must drive selection and context. Individual editing remains unrestricted by mandatory household approval. Random voice selection is deliberate.

## What the Anki Python code actually delivers

There are several generations of tooling. The database-backed Flask service is the closest baseline for the native application; the oldest word script is not the complete specification.

| Source read | Input and selection | Output |
|---|---|---|
| [Basic word script](../../scripts/vocab_to_anki-card.py) | Vocabulary text file; skips terms already in its export | Russian term, English meaning, generated image, Russian pronunciation helper, English pronunciation, HTML/media references in a tab-separated export. No systematic form selection. |
| [Sentence script](../../scripts/vocab_to_anki-card-sentence.py) | Vocabulary file and per-word sentence counters | Russian sentence; `pymorphy3` finds a form whose lemma matches the target; that surface form becomes an Anki cloze linked to OpenRussian. Adds contextual word meaning, sentence translation, sentence recording and scene image. |
| [Database sentence variant](../../scripts/vocab_to_anki-card-setence-grok.py) | `words` and their `forms`; generation caps | Matches a stored form in the sentence, blanks it, links the lemma to OpenRussian, adds contextual meaning, translated sentence, readable grammatical tags, image and sentence audio. Updates word/form counters after insertion. |
| [Active Flask Anki service](../../flask_vocab_app/services/flashcard_service.py) | Difficulty, POS, case, topics, batch size and generation cap; chooses a matching form using `ORDER BY RANDOM() LIMIT 1` | Generates a sentence for that form, formats a cloze, adds contextual meaning, sentence translation, scene image, sentence recording, stored mnemonic and Anki tags; submits the note through AnkiConnect. |
| Same service, `process_word_forms()` | One selected lemma | Iterates **all stored forms** for that lemma and generates one contextual card per form. This is an existing capability to migrate. |

The active service constructs these Anki fields:

| Field | Payload |
|---|---|
| `Text` | Russian sentence, with the matched form inside `{{c1::…}}` and an OpenRussian link to the lemma. |
| `Translation` | Target's English meaning in context. |
| `Extra` | Sentence translation, image reference and sentence `[sound:…]` reference when generated. |
| `Hint` | Lemma's saved mnemonic. |
| `Back Extra` | Empty. |
| Anki tags | POS, available case/tense/mood, form difficulty where supplied, and topics. |

The database sentence script prints the available tag dictionary into `Extra`; the active service's exported tag subset is narrower. Neither exports every grammatical feature perfectly. Exact visual placement depends on the user's Anki note templates, which were not inspected live.

Sentence speech uses the [ElevenLabs service](../../flask_vocab_app/services/elevenlabs_service.py) with a randomly selected voice. The [image prompt](../../flask_vocab_app/services/openai_service.py) illustrates the **sentence scene**. The active Anki service generates sentence audio; standalone word audio exists in the older word pipeline and has additionally been implemented natively. Scheduling, recall ratings and timers are not implemented by these generator scripts; their host reviewer supplies those behaviours.

### The API upgrade weakened the generation instructions

The working-tree diff of `flashcard_service.py` shows that the previous sequence was `generate_sentence(target_form, pos, form_tags)`, then `get_word_translation(exact_form, sentence)`, then Yandex sentence translation. The upgrade replaced those calls with `generate_native_card(..., 'ru-cloze')`.

Consolidating calls can be useful, but the prompts were not equivalent. The old prompt explicitly requested case/number usage and adjective agreement, with special imperative handling. The shared native prompt requests the supplied form exactly once and passes tags as data, but does not explicitly require or verify their grammatical use. Its `notes` field is for translation ambiguity, not a grammar explanation. **This weakened the Anki path as well as leaving the native path insufficient.**

The old prompt also had defects: its imperative branch checks `case == 'impr'`, while ordinary verb tags use `mood`; other verbs enter a generic case-oriented prompt. Repair requires POS-aware instructions and validation, not restoration of every old line.

## The lexical structure and the actual saved cards

Read-only inspection of `instance/native-flashcards-mvp/vocab.db` found **1,233 lemma/POS records and 16,049 forms**. `words.id` identifies a lemma/POS entry; `forms.word_id` references it. Uniqueness on `(word_id, form, tags)` correctly permits identical spelling with different grammatical analyses. The forms foreign-key check returned no violations.

Examples directly from this database:

| Lemma | Distinct stored learning targets |
|---|---|
| `означать` | `означает`: present, third person singular; `означают`: present, third person plural; `означала`, `означал`, `означало`: past forms. The infinitive is another target. |
| `структура` | `структуру`: accusative singular; `структурой`: instrumental singular; separate `структуры` rows for genitive singular, nominative plural and accusative plural. |
| `гроза` | Separate `грозе` rows for dative/prepositional singular; separate `грозы` rows for genitive singular, nominative plural and accusative plural. |
| `шахматы` | Plural forms `шахмат`, `шахматам`, `шахматами`, `шахматах`; separate nominative/accusative `шахматы` rows. Do not fabricate a singular paradigm. |

For example, `Мы боимся грозы` uses genitive singular, whereas `Летом часто бывают грозы` uses nominative plural. Matching the letters `грозы` alone cannot establish which one a sentence teaches.

### Media: availability is not the same as presentation or completion

There were six current published generated cards: the original five recognition cards and a new `доклад` cloze. **All six currently have an image, target-form audio and sentence audio: 18 saved media jobs.** All files were present at the configured asset-store paths, with correct byte sizes and SHA-256 hashes.

The browser loaded all six images at 1024 pixels wide and all twelve audio elements with finite durations, ready state 4 and no media errors. Opening `доклад` in the library exposed its image and audio without submitting a review. This verifies availability/loading, not the linguistic or visual quality of every asset.

The latest two-item batch saved `доклад`; **`означать` failed** with “The generated example did not use the selected word exactly once.” No card/version or media jobs were saved for that failed item. Its rejected response was not retained, so its precise offending sentence cannot be reconstructed.

The confusing experience has concrete causes:

- [Media attachment](../../flask_vocab_app/services/card_media.py) puts **every asset** on the answer side for cloze and English-to-Russian cards, including the picture. Recognition cards receive media on the prompt. This blanket rule creates inconsistent presentation.
- [Generation results](../../flask_vocab_app/ui/src/GenerateCards.tsx) show text and media status labels rather than playable/visible media previews. The library hides media behind “Look at the answer.”
- [Generation](../../flask_vocab_app/services/card_generation.py) publishes text before media finishes. The study link appears as soon as a text card is saved, and the queue does not require complete media.
- Subsequent stages are driven by requests from the open generation page. Leaving it stops further work, potentially leaving playable text with pending media.
- Batch completion means jobs are saved **or failed**. The UI warns about failed media, but terminal work is not a completed multimedia card. Omitted legacy media flags also retain text-only behaviour.

The six cards are not missing files now, but the system still permits and poorly presents incomplete cards. Readiness must be a verified state, not simply successful text generation.

## Confirmed migration defects

| Priority | Evidence | Consequence |
|---|---|---|
| P0 | `CardGenerationService.select()` sorts by `(form=lemma) DESC,id LIMIT 1`; words are selected in ID order. | Defaults prefer dictionary forms and early records instead of varying the paradigm. This reproduced the exact `означать, структура, гроза, шахматы, гуманитарный` preview. |
| P0 | At most one form per lemma is emitted. A five-card request for `word_id=7` returns only `означать`. Default `max_cards=1` excludes a lemma after one active card. | No native equivalent of generating all forms; one completed card can exclude every other form of the word. |
| P0 | Validation checks spelling/occurrence and sentence restoration; tags are copied rather than validated against the use. | An unsaved fixture labelled `грозы` genitive singular passed both `pack()` and `validate_deck()` with the nominative-plural sentence `Летом часто бывают грозы.` Reference validation checks membership/spelling, not contextual syntax. |
| P0 | Media is optional in the contract and publication precedes media completion. | Pictures/speech are not guaranteed for a card offered for study. |
| P1 | Native generation filters lemma difficulty; case is its only grammar selector. | No form-difficulty selection or number/person/tense/mood/aspect practice controls. Case alone is not a complete target. |
| P1 | For cloze, `answer` stores the Russian form; generated `english` survives only in the batch response, not as a separate card field. | Anki's contextual `Translation` field is lost from native cloze content, although the sentence translation survives. |
| P1 | Preview renders only `form`, ignoring the returned lemma/form ID/tags. The provider contract has no required grammar explanation. | The learner cannot see the intended contrast or why the ending is used. Grammar chips do not supply that explanation. |
| P1 | [Content indexing](../../flask_vocab_app/services/learning_content.py) makes every form a sibling under `word:{word_id}`; [review selection](../../flask_vocab_app/services/native_review.py) takes one sibling per session and defers others after a review that day. | Even adding several inflections would not make them available together for focused forms practice. Distinct grammatical targets are treated like duplicate views of one answer. |
| P1 | No native dictionary link or clear lemma → target relationship in the player. | The original path from sentence to lexical entry is missing. |

### Import defects that predate native flashcards

Retain the relational design. Repair its population rules:

- **All 4,710 forms attached to `ADJ` entries lack case.** [The original builder](../../vocab-list_to_schema.py) omits adjective case during extraction. [Current sync](../../flask_vocab_app/services/sync_service.py) extracts it, then explicitly removes `case` and `animacy` from adjective/participle tags during deduplication. A case filter therefore cannot select these adjective forms correctly.
- **All 897 singular past indicative forms attached to `VERB` entries lack gender.** The extraction branch omits it. Different surface strings survive, but metadata cannot reliably support feminine/masculine/neuter practice.
- Finite verbs, infinitives and gerunds share an extraction branch without retaining their form-level POS subtype. Native metadata also omits some additional participle/comparative features.
- Frequency filters and form-count limits prune paradigms. “All stored forms” does not mean “every possible form.” For example, the stored `означать` set includes third-person present forms but no first/second-person present forms. Report coverage honestly.

Changing the prompt cannot recover information discarded during import. Reconciliation must preserve IDs and ambiguous alternatives rather than replacing the relational design.

Other legacy defects must not be copied: the Anki JSON `LIKE` filter matched **zero** genitive forms where `json_extract` found **1,003**; cloze matching uses a dictionary keyed by spelling and can collapse analyses; counters can refer to the selected form rather than the matched one; repeated contexts reuse word/form media filenames. The active Anki service also accepts a note if only one of image/audio succeeds. Preserve the intended output while correcting those weaknesses.

## Corrected implementation order

1. **Select forms, then generate their contexts.** Keep word/form IDs. Support mixed forms, a grammar focus, and all eligible stored forms of one word. Snapshot the exact selection. Vary practice using native coverage per form/grammatical target, independent of Anki counters. Distinguish lemma and form difficulty. Multiple requested forms of one word must not silently collapse to one.

2. **Repair grammar additively.** Fix extraction for future imports and produce a dry-run reconciliation using the existing morphology library and source data. Preserve referenced IDs. Collapsed ambiguous rows may require additional rows and explicit card mappings, not a guessed single interpretation. Rehearse on a backup copy; preserve historical reviews. Do not use the old builder as the migration—it contains table-dropping setup.

3. **Restore one complete contextual contract for native and Anki.** Input is lemma/POS, exact form ID and grammar. Output is a natural sentence requiring that usage, target span, contextual English meaning, sentence translation and a short explanation of the grammatical choice. Validate applicable agreement/conjugation constraints. Morphological parsing establishes candidate analyses, not contextual syntax by itself. Add representative fixtures, contextual checks and bounded corrective retries; retain failure evidence privately. Do not add a universal English meaning to `words`.

4. **Require complete media before marking a generated card ready.** Persist partial work, but distinguish “preparing”/“needs retry” from ready for study. Require the sentence illustration, selected-form pronunciation and sentence recording. Preserve random voices. Use a durable local worker so leaving the page does not stop the batch; recover after restart and retry only missing stages. Repair missing media without resetting learning history.

5. **Show the learning target.** Preview `гроза → грозы · Genitive · Singular` or `означать → означают · Present · Third person · Plural`. Show the scene image with the exercise by default and make speech easy to find. Full answer-bearing speech may play on reveal or as a requested cue; assistance should not automatically force a failing recall rating. Distinguish grammar cloze with a lemma cue from vocabulary recall, so the task is understandable. Reveal the restored sentence, contextual target meaning, full translation, grammar explanation and dictionary link. Keep this automatic; manual writing is an edit option.

6. **Schedule distinct grammatical targets appropriately.** Keep per-card memory state. Group true sibling variants of the same example without blanket-burying every inflection of a lemma. Support deliberate forms practice and configurable daily limits. Separate generated-form coverage, grammar coverage and demonstrated recall. Four ratings, interval previews and accurate timing remain required in the wider parity plan.

Native study and optional Anki export should consume the **same saved contextual content and media**, with separate presentation adapters and schedules. The accessory must not receive better learning material than the main application.

## Acceptance evidence for the next pass

- Fixtures cover noun case/number, adjective agreement/animacy, verb person/number/tense/mood, past gender, aspect, plural-only nouns, indeclinables, identical spellings and uncommon forms. An aspectual partner is not automatically an inflection of the same lemma.
- `структуры` and `грозы` use the selected analysis in context; a nominative-plural sentence cannot pass as genitive singular. Identical spelling does not merge distinct form IDs.
- A five-card single-lemma request yields five eligible form/context targets when available. Grammar filters include corrected adjective cases. Preview and generation use one frozen selection.
- A completed five-card batch has **five verified pictures and ten playable Russian recordings**, without pending/failed required media hidden by a ready label. Leaving, restarting and provider retries preserve work.
- Cloze retains target meaning and sentence translation. Grammar explanation describes the actual sentence. Word audio speaks the chosen form and the image depicts the saved context.
- Several intentionally selected forms of one lemma can be practised. Media assistance does not override the learner's recall rating. Mobile and desktop checks cover image/replay placement.
- Migration preserves lexical IDs, Anki progress, native history and asset checksums. Anki Link exports the same saved form/context/media bundle without regeneration.

Verification here was source inspection, read-only SQL, unsaved selector/validation probes and browser library inspection. No paid API calls or full regression suite were run; no production implementation changed during this audit.

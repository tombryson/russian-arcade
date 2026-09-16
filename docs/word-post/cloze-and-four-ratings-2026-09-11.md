# Clozes and four review ratings

The native reviewer now uses **Again, Hard, Good, Easy**, mapped to the four actual FSRS ratings. Keyboard shortcuts are 1–4 in that order; Space reveals the answer. Using a hint remains recorded separately and does not override the selected rating. Collection history uses the same labels.

Selecting a rating saves it and automatically opens the next card, with no answer-confirmation page or Continue button. Existing sessions paused on the old confirmation screen advance on reopening. The final card leads directly to the session summary. Undo remains available on the next card until its answer is revealed, and on the automatic completion summary until another practice starts. Explicitly finishing closes undo. A failed next-card request retries that request without submitting the rating again; undo retains the review event and adds a reversal.

## Card presentation

For the owner's example:

- Front: **Я занимаюсь изучением [...] в русском языке.**, the contextual English translation **structures**, and the scene image. The blank is plain text. The Hint action uses the mnemonic saved with the vocabulary word.
- Reveal: **конструкций**, completing the Russian sentence, its contextual English meaning **structures**, **I am studying constructions in Russian.**, an optional mnemonic disclosure, and word/sentence recordings.
- Only the revealed Russian form links to **конструкция** on OpenRussian. No dictionary URL is sent with the front. The lookup uses the lemma; the answer remains the selected inflected form.

The legacy field name `cue_en` stores the contextual English meaning on the generated card, alongside its sentence and sentence translation. For a cloze this English translation appears on the front, identifying the missing word to recall. It is not labelled as a mnemonic or Hint. The card’s separate `hint` comes from `words.mnemonic` when generated. It is the provider's existing contextual `english` output, not a universal translation added to `words` or `forms`. The contextual meaning may be a phrase where English needs one. Older generated clozes recover this explicit field from their saved generation response only when the sentence, translation and selected form still match. No parser or new provider call is involved. The editor labels this field English meaning and keeps it separate from Hint.

The missing Russian answer, dictionary URL and full sentence translation are absent from the review's front response. Its contextual English word translation is present. The mnemonic stays hidden until clicked. After answer reveal it is in a collapsed Hint disclosure, unless the learner already requested it on the front. Opening this disclosure after reveal does not record assisted recall. Cloze scene images appear on the front; answer-bearing word and sentence audio appear after reveal. New generation already defaults to cloze; the optional recognition/production types remain available.

## Data changes

Migration `012_four_review_ratings.sql` widens the review-event constraint. It preserves rowids, events, reversals and existing schedules, and reinstates append-only triggers. The runner backs up the database and checks foreign keys before committing. New reviews record scheduler policy `native-fsrs-v2-four-ratings`; old policies and events are not rewritten.

The owner explicitly approved converting the five original recognition pilot cards: **что-то, вместе, юмор, зарплата, особенно**. The maintenance script `scripts/convert_native_batch_to_cloze.py` supports a dry run and an explicit `--apply`, which creates a backup and commits the replacement atomically:

1. Validate the saved generation response, exact form and all three existing media assets.
2. Create the **Sentence clozes** collection with new card identities, reusing sentences, cues, metadata, pictures and recordings.
3. Retire the five recognition cards while preserving their versions, review events and schedules.
4. Close an active queue containing those obsolete cards without submitting any rating. Start a new cloze session through the normal reviewer.

Retired cards no longer defer their active replacements through sibling spacing. Active related cards still space each other. This prevents an obsolete recognition card reviewed today from blocking its new cloze replacement.

The conversion does not call an AI provider, change lexical records, write to Anki, or regenerate media. Rerunning it recognises the existing converted collection.

## Verification and remaining work

Tests cover all four FSRS mappings and resulting learning intervals, persistence, undo, hint handling, exact-form clozes, dictionary destinations, front/back projections, cue recovery and editing, keyboard controls, collection history, and upgrade preservation including rowids and append-only guards. The five converted real cards also completed a review session on an isolated database copy, with all fifteen existing media attachments served successfully; those test ratings did not reach the user's database.

This pass does not complete all Anki parity. Interval previews, active review timing, configurable study limits, richer note/deck organisation and export remain open. The earlier Russian-content audit also remains relevant: broader stored-form selection, missing grammatical metadata, grammar-quality evaluation and reliable completion of required media need their own correction pass. A cloze layout alone does not validate Russian grammar.

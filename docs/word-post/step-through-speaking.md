# Step-through conversations

Speaking has two modes. Both use the existing scenario catalogue and A1–B2 levels.
Choose a scenario first. Its setup screen opens in Fluent conversation mode.
Two text choices above the start controls select **Fluent conversation** or
**Step-through**. An underline marks the selected mode. Changing modes preserves
the situation and level. Saved conversations keep their original mode.

| Mode | Learner action | Feedback |
|---|---|---|
| Fluent conversation | Speak freely through the microphone. | The existing audio review assesses grammar, fluency and task completion. |
| Step-through | Read or listen to one line, then choose a Russian reply. | A short explanation shows how the reply fits the situation. Hints are optional. |

Step-through teaches what to say before asking the learner to produce it freely.
Choosing a written reply is not evidence of spoken fluency or pronunciation.
The microphone is not required for this mode. Learners can say each reply aloud.

## Learner flow

1. Open Speaking, choose a scenario under its level, then select **Step-through** in its setup screen.
2. Read the situation and start the conversation. Opening a preview does not generate content.
3. Read the character's Russian line. Listen to it when audio is available.
4. Follow the short task and choose one of three Russian replies.
5. Check the reply. A wrong choice gets a specific explanation and another attempt.
6. After a correct reply, read the translation or listen to it, then continue.
7. Finish with the character's farewell and a short result. Saved conversations remain available in history.

The current exchange stays central. Earlier exchanges are secondary. The learner
does not have to scroll through the whole transcript to reach each new question.
Hints start closed and reset for every turn. An English interface gives English
instructions and explanations; the dialogue and reply choices stay in Russian.

## Reply design

Each turn needs a clear intention. “What do you want to drink?” alone cannot make
tea the only correct answer. A task such as “Ask for one tea without sugar” can.
The alternatives can ask for coffee or tea with sugar. All sound like things a
person might say, but only one meets the stated intention.

Distractors should test meaning, case, quantity, time or conversational purpose
when the distinction matters. They must not reject valid paraphrases or mark a
polite alternative wrong because the model preferred another style. Explanations
identify the useful difference in plain language. They do not invent grammar
rules to justify a choice.

One generation produces four to six exchanges and a natural ending. Every later
line follows the previous correct reply. Wrong answers are teaching attempts;
they do not silently change the situation or make the character continue from
something the learner has not yet understood.

The prompt uses the selected scenario's facts, role, goals and level. It does not
replace them with a separate café-only curriculum. Validation rejects malformed
output and repeated choices. It cannot prove that every model-generated
distinction is linguistically sound, so representative generated dialogues need
content review as well as automated tests.

The character must stay in role. A ticket clerk answers questions about departure
times and prices; they must not ask the learner those questions first. A factual
answer followed by a pause is a valid turn. Hints explain a useful Russian word
or pattern rather than repeating the task.

## Storage and requests

Migration 041 adds step-through sessions and answer attempts. It preserves the
existing live calls, recorded conversations, vocabulary and review history.
Each new session belongs to a profile and references a scenario and variant.
Its saved scenario and dialogue keep the original content even if the catalogue
changes later.

The `/api/v1/step-conversations` endpoints use the application's profile,
account-scope and CSRF checks. The server checks each chosen option; the browser
does not submit correctness or scores. Current choices have stable, shuffled IDs.
Correct answers and future turns are withheld until they are needed.

Start and answer requests carry idempotency keys. Repeating a request does not
generate another dialogue or count another attempt. A stale turn cannot advance
a newer one. Interrupted preparation has an explicit retry, and opening history
does not call a model.

Generation uses the configured conversation model through the existing provider
wrapper. Audio uses the existing speech provider. Hosted requests remain subject
to the AI switch and spending limits; account sign-in alone does not enable AI.

Audio is generated on request and cached in `step-conversation-audio/` beside the
database. Learning backups include these files and their checksums under
`step_conversation_audio`. Restore the directory beside the restored database.

## Rewards

Finishing earns up to three Lingocoins through the existing activity ledger and
shared daily cap. Repeating the same scenario variant that day does not pay
again. Hints and corrected attempts do not prevent completion rewards.

Step-through completion does not change speaking Elo, grammar scores or fluency
scores. The result describes reply-choice practice. The existing fluent mode
continues to use its independent audio assessment.

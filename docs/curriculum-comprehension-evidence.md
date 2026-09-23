# Comprehension task evidence

New A1–B2 stories save their passage, questions and reading criteria before the learner answers. The existing story library remains the entry point. Existing stories, titles, images and audio are preserved; historical feedback is not converted into new curriculum evidence.

## Reading criteria

The generator supplies four passage-based questions and a personal reflection. Each of the first four questions has one reading criterion from the selected level's reference catalogue. Its expected meaning is anchored to an exact excerpt of the passage. The reflection receives ordinary feedback but has no reading criterion.

Open answers use the application response mode `reading_response` and scope `reading_comprehension`. They do not change the source reference's `reading_selection` format. They are diagnostic evidence of understanding this passage, not independent Writing evidence or a full reading-domain result. Grammar errors should not lower a reading judgement when the intended meaning is clear.

Each frozen contract contains the complete passage and question set, the question index, expected meaning, source reference, requested topic and selected canonical topic. A topic chosen for an **Any topic** story does not reclassify the learner's vocabulary.

Assessment returns ordinary feedback plus one judgement for each frozen criterion. Scored judgements must quote the exact answer to that question. The validator rejects quotations from another answer, invented text, changed criteria and mismatched task identities. Uncertain judgements remain unscored. Provider quotation offsets may be grounded only when the quotation occurs exactly once in the original answer.

## Saving and retries

Migration `051` adds two tables:

| Table | Purpose |
| --- | --- |
| `comprehension_tasks` | Owned, immutable passage and question-set versions. |
| `comprehension_attempts` | Exact answers, feedback, support and request identity for each successful check. |

The shared `activity_task_contracts` and `activity_criterion_reports` tables hold the question criteria and results. The story row keeps the latest library view. Each check saves its answers, reports and existing participation reward in one transaction. A failed or stale check saves none of them.

Repeated requests reuse the saved result. Checking unchanged answers also reuses feedback without another provider call. Short operation leases prevent duplicate assessment and extra-question calls across tabs. Each provider attempt has its own token, so an expired request cannot clear or commit a replacement request. Failed requests release the lease; an interrupted process leaves a lease that expires after three minutes.

Adding questions creates a new task version. The four original reading criteria are reissued against that question set; extra questions receive ordinary feedback only. Earlier contracts and attempts remain unchanged. An older open form cannot overwrite the newer question set. Feedback exposure carries forward as `model_answer` support.

All reads and writes check the current profile and story ownership. Editable hidden fields cannot replace a contracted passage, questions, level or media. Removing the task identity from a new form does not permit a fallback write through the older story path.

The existing Journey preparation and skill-estimate adapters read the saved attempt. They derive the topic, score and earlier-feedback exposure from that record, not from event claims. Corrections can still contribute topic preparation; they do not create another first-check Elo result. Daily coin caps do not stop eligible practice evidence. These compatibility adapters do not turn a reading criterion into a course pass.

## Support and listening

Later checks record that earlier feedback was available. Word-translation use is not yet recorded for these generated tasks, so an empty support list does **not** establish independence.

The ordinary Comprehension page shows the passage and offers audio of the same text. These checks therefore produce reading evidence only. Listening evidence requires an audio-first task with tracked transcript, translation and playback support. The authored teaching-unit listening player already supplies that foundation; the generated-story adapter remains future work.

## Migration and limits

Account import preserves frozen payloads and UUIDs, remaps the story's relational ID where necessary, and validates task ownership, question criteria, attempts, reports and revision history. An imported in-flight check lease is cleared so it cannot block practice in the destination. Source databases remain unchanged.

Legacy stories and C1/C2 generation retain their existing feedback path. There is no retrospective marking, new level gate, vocabulary insertion or change to the generation model, voice selection, account controls or demo spending limits.

Automated checks cover persistence, retries, stale forms, profile isolation, provider schemas, exact response evidence, transactional failure and import integrity. They establish software behavior, not linguistic validity. Qualified review must still check passage-question alignment, level suitability, inference quality and agreement with human marking. A saved excerpt alone cannot establish that a generated inference is justified.

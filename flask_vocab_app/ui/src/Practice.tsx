import { useEffect, useRef, useState } from 'preact/hooks';
import { api, ApiError, type PracticeSession } from './learning-api';
import { Feedback, Sheet } from './components';

export function Practice({ sessionId, profileId, onFinish }: { sessionId: string; profileId: string; onFinish: () => void }) {
  const [saved, setSaved] = useState<PracticeSession>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState(true);
  const [reload, setReload] = useState(0);
  const [blocked, setBlocked] = useState(false);
  const pending = useRef<{ url: string; body: object }>();
  const controller = useRef<AbortController>();
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const request = new AbortController(); controller.current = request;
    setSaved(undefined); setError(''); setBlocked(false);
    void api<PracticeSession>(`/api/v1/learning-sessions/${sessionId}`, undefined, request.signal).then(value => {
      if (value.profile_id !== profileId) throw new Error('Choose the learner who started this activity.');
      setSaved(value); setFeedback(true);
    }).catch(reason => { if (!request.signal.aborted) setError(reason instanceof Error ? reason.message : 'This activity could not open.'); });
    return () => request.abort();
  }, [sessionId, profileId, reload]);
  useEffect(() => { heading.current?.focus(); }, [saved?.completed_items, feedback]);

  async function submit(operation: 'attempts' | 'help', choiceId?: string) {
    if (!saved?.item || busy || blocked) return;
    if (!pending.current) pending.current = { url: `/api/v1/learning-sessions/${sessionId}/${operation}`, body: {
      submission_id: crypto.randomUUID(), expected_revision: saved.revision, item_id: saved.item.id,
      ...(operation === 'attempts' ? { answer: { choice_id: choiceId } } : {}),
    } };
    setBusy(true); setError('');
    try {
      const result = await api<PracticeSession>(pending.current.url, pending.current.body, controller.current?.signal);
      if (result.profile_id !== profileId) throw new Error('The learner changed. Open this activity again.');
      pending.current = undefined; setSaved(result); setFeedback(operation === 'attempts');
    } catch (reason) {
      if (controller.current?.signal.aborted) return;
      if (reason instanceof ApiError && reason.code === 'stale_revision' && reason.currentSession?.profile_id === profileId) {
        pending.current = undefined; setSaved(reason.currentSession); setFeedback(true);
        setError('Practice changed in another tab. The latest saved answer is shown here.');
      } else if (reason instanceof ApiError && ['locked', 'profile_changed', 'access_required', 'adult_required', 'learner_required', 'content_unavailable', 'not_found', 'csrf_failed'].includes(reason.code)) {
        pending.current = undefined; setBlocked(true); setSaved(undefined); setError(reason.message);
      } else setError('We could not confirm the save. Your answer is still here. Try saving again.');
    } finally { if (!controller.current?.signal.aborted) setBusy(false); }
  }

  const last = saved?.attempts.at(-1)?.feedback;
  const showResult = feedback && last;
  return <section class="page practice-page"><div class="lesson-head"><a class="text-link" href="#activities">Back to activities</a><span class="quiet">{busy ? 'Saving…' : pending.current ? 'Save not confirmed' : saved ? 'Progress saved on this computer' : ''}</span></div>
    {!saved ? <><h1 ref={heading} tabIndex={-1}>{error ? 'This activity could not open.' : 'Opening your practice…'}</h1>{error ? <><p role="alert">{error}</p><div class="action-row">{!blocked && <button class="cta" onClick={() => { pending.current = undefined; setReload(value => value + 1); }}>Try again</button>}<a href="/post/household">Choose a learner</a></div></> : <p role="status">Loading your saved answers.</p>}</>
      : <><p class="kicker">{saved.title}</p><h1 ref={heading} tabIndex={-1}>{showResult ? last.outcome === 'correct' ? 'That’s right.' : 'Let’s look at the answer.' : saved.status === 'completed' ? 'Practice complete.' : `Question ${saved.completed_items + 1} of ${saved.total_items}`}</h1>
        {showResult ? <Sheet>{saved.attempts.at(-1)?.prompt && <p class="practice-prompt">{saved.attempts.at(-1)?.prompt}</p>}<p class="answer-label">{last.outcome === 'correct' ? 'Your answer' : 'The correct answer'}</p><p class="answer-text">{last.answer}</p><p>{last.assisted ? 'You used a hint for this question.' : 'Your answer has been saved.'}</p><button class="cta" onClick={() => setFeedback(false)}>{saved.status === 'completed' ? 'Finish practice' : 'Next question'} <span aria-hidden="true">→</span></button></Sheet>
          : saved.status === 'completed' ? <Sheet><h2>You answered {saved.total_items} {saved.total_items === 1 ? 'question' : 'questions'}.</h2><p>Your answers are saved. Choose another activity when you’re ready.</p><details class="answer-history"><summary>Review your answers</summary><ol>{saved.attempts.map(attempt => <li key={attempt.id}>{attempt.feedback.answer} — {attempt.feedback.outcome === 'correct' ? 'answered correctly' : 'answer shown'}{attempt.feedback.assisted ? ' with a hint' : ''}</li>)}</ol></details><button class="cta" onClick={onFinish}>Back to activities</button></Sheet>
            : saved.item && <Sheet><h2 class="practice-prompt">{saved.item.prompt}</h2><p>Choose one answer.</p>
              <div class="options">{saved.item.choices.map(choice => <button key={choice.id} class="word" disabled={busy || !!pending.current} onClick={() => void submit('attempts', choice.id)}>{choice.text}</button>)}</div>
              {saved.item.has_hint && !saved.item.hint && <button class="text-link" disabled={busy || !!pending.current} onClick={() => void submit('help')}>Show a hint</button>}
              {saved.item.hint && <Feedback>{saved.item.hint}</Feedback>}
              {!!saved.item.asset_ids?.length && <div class="activity-media">{saved.item.asset_ids.map((id, index) => <a key={id} class="text-link" href={`/api/v1/assets/${id}`} target="_blank" rel="noopener">Open supporting picture or audio {index + 1}</a>)}</div>}
            </Sheet>}
        {error && <div role="alert" class="error-note"><p>{error}</p>{pending.current && <button class="cta" disabled={busy} onClick={() => void submit(pending.current!.url.endsWith('/help') ? 'help' : 'attempts')}>Try saving again</button>}</div>}
      </>}
  </section>;
}

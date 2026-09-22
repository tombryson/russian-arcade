import {useEffect,useRef,useState} from 'preact/hooks';
import {api,ApiError} from './learning-api';
import type {Language} from './review-types';
import type {ProgressionState} from './Progression';
import './styles/course-journey.css';

export type CourseTopic={id:string;title:string;title_ru:string;completed:boolean;successful_tasks:number;required_tasks:number;links:{activity:string;label:string;label_ru:string;href:string}[]};
export type CourseChapter={objectives?:{en:string;ru:string}[];preparation?:{topic_id:string;title:string;title_ru:string;explanation:string;explanation_ru:string;examples:{ru:string;en:string}[]}[];id:string;number:number;title:string;title_ru:string;intro:string;intro_ru:string;status:'locked'|'practice'|'ready'|'passed';progress:number;topics:CourseTopic[];activity_count:number;required_activity_count:number;last_attempt_id:string|null};
export type CourseData={version:string|number;profile_id:string;band:'A1';unlocked_levels:string[];current_chapter_id:string|null;progress:number;completed:boolean;chapters:CourseChapter[]};
export type CourseAttempt={glossary?:{ru:string;en:string}[];id:string;chapter_id:string;chapter_number:number;title:string;title_ru:string;letter:string;letter_title:string;letter_title_ru:string;listening:{audio_url:string;transcript?:string};questions:{id:string;prompt:string;prompt_ru:string;choices:{id:string;text:string}[];kind:'reading'|'listening'|'response';hint?:string;hint_ru?:string}[];status:'active'|'passed'|'retry';support_used:boolean;listened:boolean;result?:{score:number;total:number;passed:boolean;essential_passed?:boolean;feedback:{question_id:string;correct:boolean;answer:string;selected_answer?:string;explanation:string;explanation_ru:string}[]};course:CourseData};
type Submission={answers:Record<string,string>;submission_id:string};
type Draft={answers:Record<string,string>;pending?:Submission};
const storagePrefix='word-post:checkpoint:';
const clamp=(value:number)=>Number.isFinite(value) ? Math.max(0,Math.min(1,value)) : 0;
const draftKey=(profile:string,attempt:string)=>`${storagePrefix}${encodeURIComponent(profile)}:${encodeURIComponent(attempt)}`;
function readDraft(profile:string,attempt:string):Draft {
  try {const saved=JSON.parse(sessionStorage.getItem(draftKey(profile,attempt)) || '{}');return {answers:saved.answers || {},pending:saved.pending};} catch {return {answers:{}};}
}
function writeDraft(profile:string,attempt:string,value?:Draft) {
  try {if (value) sessionStorage.setItem(draftKey(profile,attempt),JSON.stringify(value));else sessionStorage.removeItem(draftKey(profile,attempt));} catch { /* Storage may be disabled; the current page still works. */ }
}
function clearOtherProfiles(profile:string) {
  try {for (let index=sessionStorage.length-1;index>=0;index--) {const key=sessionStorage.key(index);if (key?.startsWith(storagePrefix) && !key.startsWith(`${storagePrefix}${encodeURIComponent(profile)}:`)) sessionStorage.removeItem(key);}} catch { /* Storage is optional. */ }
}

export function CourseJourney({chapterId,attemptId,language='en',progression}:{chapterId?:string;attemptId?:string;language?:Language;progression:ProgressionState}) {
  const t=(en:string,ru:string)=>language==='ru' ? ru : en;
  const profile=progression.data?.profile_id;
  const identity=`${profile ?? ''}:${chapterId ?? ''}:${attemptId ?? ''}`;
  const currentIdentity=useRef(identity);currentIdentity.current=identity;
  const loadedIdentity=useRef('');
  const [course,setCourse]=useState<CourseData>();
  const [attempt,setAttempt]=useState<CourseAttempt>();
  const [answers,setAnswers]=useState<Record<string,string>>({});
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(true);
  const [busy,setBusy]=useState('');
  const [revision,setRevision]=useState(0);
  const pending=useRef<Submission>();
  const startRequest=useRef<{chapter:string;challenge:boolean;request_id:string}>();
  const inFlight=useRef(false);
  const listeningReceiptPending=useRef(false);
  const resultSummary=useRef<HTMLElement>(null);
  const focusResultOnSave=useRef(false);
  useEffect(()=>{
    const abort=new AbortController();setLoading(true);setCourse(undefined);setAttempt(undefined);setAnswers({});setError('');setBusy('');pending.current=undefined;startRequest.current=undefined;inFlight.current=false;listeningReceiptPending.current=false;focusResultOnSave.current=false;
    if (profile) clearOtherProfiles(profile);
    const load=attemptId ? api<CourseAttempt>(`/api/v1/course/checkpoints/${encodeURIComponent(attemptId)}`,undefined,abort.signal) : api<CourseData>('/api/v1/course',undefined,abort.signal);
    void load.then(value=>{
      if (abort.signal.aborted || currentIdentity.current!==identity) return;
      const loaded='course' in value ? value.course : value;
      if (profile && loaded.profile_id!==profile) throw new ApiError(t('The learner changed. Reload your journey.','Профиль изменился. Загрузите путешествие заново.'),'profile_changed');
      clearOtherProfiles(loaded.profile_id);loadedIdentity.current=identity;setCourse(loaded);
      if ('course' in value) {
        setAttempt(value);
        if (value.status==='active') {const draft=readDraft(loaded.profile_id,value.id);setAnswers(draft.answers);pending.current=draft.pending;}
        else {setAnswers(Object.fromEntries((value.result?.feedback ?? []).filter(item=>item.selected_answer).map(item=>[item.question_id,item.selected_answer!])));writeDraft(loaded.profile_id,value.id);}
      }
    }).catch(e=>{if (!abort.signal.aborted && currentIdentity.current===identity) setError(e instanceof Error ? e.message : t('Your journey could not load.','Не удалось загрузить путешествие.'));})
      .finally(()=>{if (!abort.signal.aborted && currentIdentity.current===identity) setLoading(false);});
    return ()=>abort.abort();
  },[identity,revision]);
  const visibleCourse=loadedIdentity.current===identity && course && (!profile || course.profile_id===profile) ? course : undefined;
  const visibleAttempt=visibleCourse && attempt?.id===attemptId ? attempt : undefined;
  useEffect(()=>{
    if (!focusResultOnSave.current || !visibleAttempt?.result || !resultSummary.current) return;
    focusResultOnSave.current=false;
    resultSummary.current.focus({preventScroll:true});
    resultSummary.current.scrollIntoView?.({block:'start'});
  },[visibleAttempt?.id,visibleAttempt?.status]);
  const chapter=visibleCourse?.chapters.find(item=>item.id===(chapterId ?? visibleAttempt?.chapter_id ?? visibleCourse.current_chapter_id));
  const failure=(e:unknown)=>e instanceof Error ? e.message : t('This could not be saved. Please try again.','Не удалось сохранить. Попробуйте ещё раз.');
  function showFailure(e:unknown) {
    if (e instanceof ApiError && ['locked','profile_changed','profile_required','adult_required','unauthorized'].includes(e.code)) {
      if (visibleCourse && visibleAttempt) writeDraft(visibleCourse.profile_id,visibleAttempt.id);
      setCourse(undefined);setAttempt(undefined);setAnswers({});pending.current=undefined;
    }
    setError(failure(e));
  }
  function accept(value:CourseAttempt) {
    if (value.course.profile_id!==visibleCourse?.profile_id) throw new ApiError(t('The learner changed. Reload your journey.','Профиль изменился. Загрузите путешествие заново.'),'profile_changed');
    setAttempt(value);setCourse(value.course);
  }
  async function start(selected:CourseChapter,challenge=false) {
    if (inFlight.current || !visibleCourse) return;
    const owner=identity;inFlight.current=true;setBusy('start');setError('');
    if (startRequest.current?.chapter!==selected.id || startRequest.current.challenge!==challenge) startRequest.current={chapter:selected.id,challenge,request_id:crypto.randomUUID()};
    try {
      const value=await api<CourseAttempt>(`/api/v1/course/chapters/${encodeURIComponent(selected.id)}/checkpoint`,{request_id:startRequest.current.request_id,...(challenge ? {challenge:true} : {})});
      if (currentIdentity.current!==owner) return;
      accept(value);progression.refresh();window.location.hash=`journey/checkpoint/${encodeURIComponent(value.id)}`;
    } catch(e) {if (currentIdentity.current===owner) showFailure(e);}
    finally {if (currentIdentity.current===owner) {inFlight.current=false;setBusy('');}}
  }
  async function checkpointAction(action:'answer'|'support'|'listened',body:unknown) {
    if (!visibleAttempt || inFlight.current || !visibleCourse) return;
    const owner=identity;inFlight.current=true;setBusy(action);setError('');
    if (action==='listened') listeningReceiptPending.current=false;
    try {
      const value=await api<CourseAttempt>(`/api/v1/course/checkpoints/${encodeURIComponent(visibleAttempt.id)}/${action}`,body);
      if (currentIdentity.current!==owner) return;
      if (action==='answer' && visibleAttempt.status==='active' && value.status!=='active') focusResultOnSave.current=true;
      accept(value);
      if (value.status!=='active') {pending.current=undefined;writeDraft(value.course.profile_id,value.id);progression.refresh();}
    } catch(e) {if (currentIdentity.current===owner) showFailure(e);}
    finally {if (currentIdentity.current===owner) {inFlight.current=false;setBusy('');if (action!=='listened' && listeningReceiptPending.current) void checkpointAction('listened',{});}}
  }
  function choose(question:string,choice:string) {
    if (!visibleAttempt || !visibleCourse || pending.current || visibleAttempt.status!=='active') return;
    const next={...answers,[question]:choice};setAnswers(next);writeDraft(visibleCourse.profile_id,visibleAttempt.id,{answers:next});
  }
  function submit() {
    if (!visibleAttempt || !visibleCourse || inFlight.current) return;
    if (!pending.current) pending.current={answers:{...answers},submission_id:crypto.randomUUID()};
    writeDraft(visibleCourse.profile_id,visibleAttempt.id,{answers,pending:pending.current});
    void checkpointAction('answer',pending.current);
  }
  const stateText=(status:CourseChapter['status'])=>status==='passed' ? t('Passed','Пройдено') : status==='ready' ? t('Checkpoint ready','Можно пройти проверку') : status==='locked' ? t('Coming next','Впереди') : t('In practice','Практика');
  const position=(number:number)=>t(`Chapter ${number} of ${visibleCourse?.chapters.length ?? 4}`,`Глава ${number} из ${visibleCourse?.chapters.length ?? 4}`);
  function topicList(selected:CourseChapter) {
    return <ul class="course-topics">{selected.topics.map(topic=><li key={topic.id}>
      <div class="course-topic-heading"><h3>{t(topic.title,topic.title_ru)}</h3><span class="quiet">{topic.completed ? t('✓ Practised','✓ Практика завершена') : t(`${topic.successful_tasks}/${topic.required_tasks} successful tasks`,`${topic.successful_tasks}/${topic.required_tasks} успешных заданий`)}</span></div>
      {selected.preparation?.filter(item=>item.topic_id===topic.id).map(item=><div class="course-preparation" key={item.topic_id}><p>{t(item.explanation,item.explanation_ru)}</p><dl>{item.examples.map(example=><div key={example.ru}><dt lang="ru">{example.ru}</dt><dd>{example.en}</dd></div>)}</dl></div>)}
      <div class="course-practice-links">{topic.links.map(link=><a key={`${topic.id}:${link.activity}`} href={link.href}>{t(link.label,link.label_ru)} →</a>)}</div>
    </li>)}</ul>;
  }
  function chapterAction(selected:CourseChapter) {
    if (selected.status==='locked') return <p class="quiet">{t('Pass the previous chapter’s checkpoint to continue. You can practise any time.','Пройдите проверку предыдущей главы. Практика доступна в любое время.')}</p>;
    if (selected.status==='passed') return <>{selected.last_attempt_id && <a class="text-link" href={`#journey/checkpoint/${encodeURIComponent(selected.last_attempt_id)}`}>{t('View checkpoint result','Посмотреть результат проверки')} →</a>}</>;
    return <div class="course-checkpoint-entry">
      {selected.status==='ready' ? <><p>{t('Your practice is complete. Read a message, listen, and choose your reply.','Практика завершена. Прочитайте сообщение, послушайте и выберите ответ.')}</p><button class="cta" disabled={!!busy} onClick={()=>void start(selected)}>{busy==='start' ? t('Opening…','Открываем…') : t('Start checkpoint','Начать проверку')} →</button></> : <><p class="quiet">{t('Practise these topics to prepare for a short checkpoint. Already know them? You can test out now.','Потренируйте эти темы перед короткой проверкой. Уже знакомы с ними? Пройдите проверку сейчас.')}</p><button class="live-mute" disabled={!!busy} onClick={()=>void start(selected,true)}>{busy==='start' ? t('Opening…','Открываем…') : t('Test out of this chapter','Пройти главу без подготовки')} →</button></>}
      {selected.last_attempt_id && <a class="text-link" href={`#journey/checkpoint/${encodeURIComponent(selected.last_attempt_id)}`}>{t('Open saved checkpoint','Открыть сохранённую проверку')}</a>}
    </div>;
  }
  return <section class="page course-page">
    <nav class="course-navigation" aria-label={t('Journey navigation','Навигация по путешествию')}><a class="text-link" href={attemptId ? `#journey/chapter/${encodeURIComponent(visibleAttempt?.chapter_id ?? '')}` : chapterId ? '#journey' : '#activities'}>← {attemptId ? t('Chapter practice','Практика главы') : chapterId ? t('Your journey','Ваше путешествие') : t('All activities','Все занятия')}</a><a class="text-link" href="/curriculum">{t('Choose practice level','Выбрать уровень практики')}</a></nav>
    {loading && <p role="status">{t('Opening your journey…','Открываем ваше путешествие…')}</p>}
    {error && <div class="course-error"><p class="error-note" role="alert">{error}</p>{!visibleCourse && <button class="live-mute" onClick={()=>setRevision(value=>value+1)}>{t('Try again','Попробовать ещё раз')}</button>}</div>}
    {!loading && visibleCourse && (attemptId ? visibleAttempt && <>
      <header class="course-heading"><p class="kicker">A1 · {position(visibleAttempt.chapter_number)} · {t('Checkpoint','Проверка')}</p><h1>{t(visibleAttempt.title,visibleAttempt.title_ru)}</h1><p class="quiet">{t('Read the message, listen to the short recording, then answer.','Прочитайте сообщение, послушайте короткую запись и ответьте.')}</p></header>
      <div class="course-checkpoint-layout">
        <article class="course-letter" aria-label={t(visibleAttempt.letter_title,visibleAttempt.letter_title_ru)}><div class="course-letter-mark" aria-hidden="true"><span>✉</span><img src="/static/images/barsik-running-v1.webp" alt="" width="74" height="55" /></div><p class="kicker">{t(visibleAttempt.letter_title,visibleAttempt.letter_title_ru)}</p><div class="course-letter-text" lang="ru">{visibleAttempt.letter}</div>{!!visibleAttempt.glossary?.length && <details class="course-glossary"><summary>{t('Useful words','Полезные слова')}</summary><dl>{visibleAttempt.glossary.map(word=><div key={word.ru}><dt lang="ru">{word.ru}</dt><dd>{word.en}</dd></div>)}</dl></details>}<p class="course-letter-signoff" aria-hidden="true">ПОЧТА · {visibleAttempt.chapter_number.toString().padStart(2,'0')}</p></article>
        <form class="course-questions" onSubmit={event=>{event.preventDefault();submit();}}>
          {visibleAttempt.questions.map((question,index)=>{
            const correction=visibleAttempt.result?.feedback.find(item=>item.question_id===question.id);
            const showAudio=question.kind==='listening' && visibleAttempt.questions.find(item=>item.kind==='listening')?.id===question.id;
            return <div class="course-question" key={question.id}>
              {showAudio && <section class="course-listening" aria-label={t('Listening recording','Аудиозапись')}><h2>{t('Listen to the message','Послушайте сообщение')}</h2><audio aria-label={t('Checkpoint recording','Запись для проверки')} controls preload="none" src={visibleAttempt.listening.audio_url} onEnded={()=>{if (!visibleAttempt.listened && visibleAttempt.status==='active') {listeningReceiptPending.current=true;void checkpointAction('listened',{});}}} />
                <p class="quiet">{visibleAttempt.listened ? t('✓ Recording heard. You can replay it.','✓ Запись прослушана. Можно включить её снова.') : t('Listen to the full recording before submitting.','Послушайте запись до конца перед отправкой.')}</p>
                {visibleAttempt.listening.transcript ? <p class="course-support" lang="ru">{visibleAttempt.listening.transcript}</p> : <button type="button" class="text-button" disabled={!!busy || !!pending.current || visibleAttempt.status!=='active'} onClick={()=>void checkpointAction('support',{kind:'transcript'})}>{t('Read transcript · practice only','Читать текст записи · с поддержкой')}</button>}
              </section>}
              <fieldset disabled={!!busy || !!pending.current || visibleAttempt.status!=='active'}><legend><span>{index+1}.</span> {t(question.prompt,question.prompt_ru)}</legend><div class="course-choices">{question.choices.map(choice=><label class={`course-choice${answers[question.id]===choice.id ? ' is-selected' : ''}`} key={choice.id}><input type="radio" name={`course-${visibleAttempt.id}-${question.id}`} value={choice.id} checked={answers[question.id]===choice.id} onChange={()=>choose(question.id,choice.id)} /><span lang="ru">{choice.text}</span></label>)}</div></fieldset>
              {visibleAttempt.status==='active' && (question.hint ? <p class="course-support">{t(question.hint,question.hint_ru || question.hint)}</p> : <button class="text-button" type="button" disabled={!!busy || !!pending.current} onClick={()=>void checkpointAction('support',{kind:'hint',question_id:question.id})}>{t('Get a hint · practice only','Подсказка · с поддержкой')}</button>)}
              {correction && <div class={`course-correction${correction.correct ? ' is-correct' : ''}`}><strong>{correction.correct ? t('✓ Correct','✓ Верно') : t('Try this answer:','Верный ответ:')} {!correction.correct && <span lang="ru">{question.choices.find(choice=>choice.id===correction.answer)?.text}</span>}</strong><p>{t(correction.explanation,correction.explanation_ru)}</p></div>}
            </div>;
          })}
          {visibleAttempt.status==='active' ? <div class="course-submit"><p class="quiet">{visibleAttempt.support_used ? t('Support used: this is a practice attempt. Try a fresh checkpoint without support to pass.','Вы использовали поддержку: это тренировочная попытка. Чтобы пройти главу, повторите проверку без подсказок.') : t('Hints and the transcript are always available. Using either makes this a practice attempt.','Подсказки и текст записи доступны всегда. С ними попытка становится тренировочной.')}</p><button class="cta" type="submit" disabled={!!busy || !visibleAttempt.listened || !visibleAttempt.questions.every(question=>answers[question.id])}>{busy==='answer' ? t('Saving answers…','Сохраняем ответы…') : pending.current ? t('Retry saving answers','Повторить сохранение ответов') : t('Check my answers','Проверить ответы')}</button>{pending.current && !busy && <p class="quiet">{t('Your selected answers are held while saving is retried.','Ваши ответы сохранены для повторной отправки.')}</p>}</div> : visibleAttempt.result && <section class="course-result" ref={resultSummary} tabIndex={-1} aria-label={t('Checkpoint result','Результат проверки')} aria-live="polite"><p class="kicker">{visibleAttempt.result.score}/{visibleAttempt.result.total} {t('correct','верно')}</p><h2>{visibleAttempt.result.passed ? t('Chapter passed','Глава пройдена') : t('A little more practice','Ещё немного практики')}</h2><p>{visibleAttempt.result.passed ? t('Your progress is saved. You’re ready for the next part of the journey.','Прогресс сохранён. Можно продолжать путешествие.') : visibleAttempt.support_used ? t('Good practice with support. To pass, try a fresh version without hints or the transcript.','Вы потренировались с поддержкой. Чтобы пройти главу, попробуйте новый вариант без подсказок и текста записи.') : visibleAttempt.result.essential_passed===false ? t('One key detail needs another look. Review the corrections and try again.','Ещё одна важная деталь требует внимания. Посмотрите исправления и попробуйте снова.') : t('Review the corrections above, practise the topics, and try a different message.','Посмотрите исправления, потренируйте темы и попробуйте другое сообщение.')}</p><div class="course-result-actions">{visibleAttempt.result.passed ? <a class="cta" href={visibleCourse.completed ? '/curriculum#level-A2' : '#journey'}>{visibleCourse.completed ? t('Explore A2 practice','Перейти к практике A2') : t('Continue the journey','Продолжить путешествие')} →</a> : chapter && <button type="button" class="cta" disabled={!!busy} onClick={()=>void start(chapter,chapter.status==='practice')}>{busy==='start' ? t('Opening…','Открываем…') : t('Try a different checkpoint','Попробовать другую проверку')} →</button>}<a class="text-link" href={`#journey/chapter/${encodeURIComponent(visibleAttempt.chapter_id)}`}>{t('Practise this chapter','Практика этой главы')}</a></div></section>}
        </form>
      </div>
    </> : chapterId ? chapter ? <>
      <header class="course-heading"><p class="kicker">A1 · {position(chapter.number)} · {stateText(chapter.status)}</p><h1>{t(chapter.title,chapter.title_ru)}</h1><p>{t(chapter.intro,chapter.intro_ru)}</p>{!!chapter.objectives?.length && <ul class="course-objectives">{chapter.objectives.map(item=><li key={item.en}>{t(item.en,item.ru)}</li>)}</ul>}</header>
      <div class="course-chapter-progress"><progress max={1} value={clamp(chapter.progress)} aria-label={t('Chapter progress','Прогресс главы')} /><span>{Math.round(clamp(chapter.progress)*100)}%</span></div>
      {chapterAction(chapter)}<p class="quiet course-readiness">{t('Complete two successful tasks for each topic, using at least two activities.','Выполните два успешных задания по каждой теме, используя как минимум два вида занятий.')} {chapter.activity_count}/{chapter.required_activity_count} {t('activities used','видов занятий использовано')}.{chapter.topics.every(topic=>topic.completed) && chapter.activity_count<chapter.required_activity_count && <> {t('Try another activity, such as Writing or Speaking, to finish preparing.','Попробуйте другой вид занятий, например письмо или разговор, чтобы завершить подготовку.')}</>}</p><h2 class="course-section-title">{t('Practise the chapter','Практика главы')}</h2>{topicList(chapter)}
    </> : <p role="alert">{t('This chapter could not be found.','Глава не найдена.')}</p> : <>
      <header class="course-heading course-overview-heading"><div><p class="kicker">{t('Your A1 journey','Ваше путешествие A1')}</p><h1>{visibleCourse.completed ? t('Your letter has arrived','Ваше письмо доставлено') : t('A letter to discover','Письмо ждёт вас')}</h1><p>{visibleCourse.completed ? t('All four chapters passed. A2 practice is now available.','Все четыре главы пройдены. Теперь доступна практика A2.') : t('Four chapters with Barsik. Practise Russian, understand small messages, and open your original letter in the final chapter.','Четыре главы с Барсиком. Практикуйте русский, читайте короткие сообщения и откройте ваше первое письмо в последней главе.')}</p></div><img src="/static/images/barsik-running-v1.webp" alt="" width="110" height="81" /></header>
      {visibleCourse.completed && <a class="cta" href="/curriculum#level-A2">{t('Explore A2 practice','Перейти к практике A2')} →</a>}
      {chapter && !visibleCourse.completed && <div class="course-next"><div><p class="kicker">{position(chapter.number)} · {stateText(chapter.status)}</p><h2>{t(chapter.title,chapter.title_ru)}</h2></div><a class="cta" href={`#journey/chapter/${encodeURIComponent(chapter.id)}`}>{chapter.status==='ready' ? t('Open checkpoint','Открыть проверку') : t('Continue chapter','Продолжить главу')} →</a></div>}
      <ol class="course-chapters">{visibleCourse.chapters.map(item=><li class={`course-chapter is-${item.status}`} key={item.id}><span class="course-chapter-number" aria-hidden="true">{item.status==='passed' ? '✓' : item.number}</span><div><p class="kicker">{position(item.number)} · {stateText(item.status)}</p><h2><a href={`#journey/chapter/${encodeURIComponent(item.id)}`}>{t(item.title,item.title_ru)}</a></h2><p>{t(item.intro,item.intro_ru)}</p>{item.status!=='locked' && <div class="course-chapter-progress"><progress max={1} value={clamp(item.progress)} aria-label={t(`Chapter ${item.number} progress`,`Прогресс главы ${item.number}`)} /><span>{Math.round(clamp(item.progress)*100)}%</span></div>}</div></li>)}</ol>
      <p class="course-practice-note"><a class="text-link" href="#activities">{t('Browse all practice activities','Все занятия для практики')} →</a><span>{t('Practice is always available. Your skill ratings stay in your profile.','Практика доступна всегда. Рейтинги навыков — в вашем профиле.')}</span></p>
    </>)}
  </section>;
}

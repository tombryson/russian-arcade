import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import { api, ApiError } from './learning-api';
import { ActivityHeader } from './ActivityHeader';
import type { Language } from './review-types';
import type { PracticeLevel } from './Progression';
import './styles/step-through-conversation.css';

type Localized = {en:string;ru:string};
type Line = {russian:string;english:string};
type Scenario = {title:string;title_ru?:string;description?:string;description_ru?:string;role?:string;role_ru?:string;seed:string};
type Step = {
  id:string;ordinal:number;npc:Line;intent:Localized;options:{id:string;russian:string}[];
  hint:Localized|null;answered:boolean;
  feedback:{option_id:string;correct:boolean;explanation:Localized;english:string}|null;
  npc_audio_url:string|null;reply_audio_url:string|null;
};
export type StepConversation = {
  id:string;state:'preparing'|'active'|'completed'|'failed';scenario:Scenario;target_level:PracticeLevel;
  language:Language;created_at:number;error:string|null;retryable:boolean;turn_count:number;completed_turns:number;
  current_turn:Step|null;transcript:{id:string;ordinal:number;npc:Line;reply:Line}[];ending?:Line;
  audio_configured?:boolean;reward?:{amount:number;basis:string}|null;
};
type Options = {configured:boolean;audio_configured:boolean;scenario:Scenario|null;sessions:{id:string;state:string;created_at:number;title:string;title_ru?:string;target_level:PracticeLevel}[]};
type Command = {kind:'start'|'answer'|'hint'|'next'|'retry'|'npc'|'reply';url:string;body:Record<string,unknown>};
type Props = {sessionId?:string;scenarioId?:string;scenarioSeed?:string;targetLevel?:PracticeLevel;language?:Language;onBack?:()=>void};
const endpoint='/api/v1/step-conversations';

export function StepThroughConversation({sessionId,scenarioId,scenarioSeed,targetLevel='A1',language='en',onBack}:Props) {
  const t=(en:string,ru:string)=>language==='ru' ? ru : en;
  const local=(value:Localized)=>language==='ru' ? value.ru : value.en;
  const [options,setOptions]=useState<Options>();
  const [saved,setSaved]=useState<StepConversation>();
  const [loading,setLoading]=useState(true);
  const [busy,setBusy]=useState<Command['kind']|null>(null);
  const [selected,setSelected]=useState('');
  const [error,setError]=useState('');
  const [retryCommand,setRetryCommand]=useState<Command|null>(null);
  const [needsReload,setNeedsReload]=useState(false);
  const [accountChanged,setAccountChanged]=useState(false);
  const [audioNotice,setAudioNotice]=useState('');
  const [playing,setPlaying]=useState<'npc'|'reply'|null>(null);
  const playbackRequest=useRef(0);
  const controller=useRef<AbortController>();
  const generation=useRef(0);
  const inFlight=useRef(false);
  const currentTurn=useRef<string>();
  const startKey=useRef(crypto.randomUUID());
  const focusTarget=useRef<'turn'|'feedback'|null>(null);
  const prompt=useRef<HTMLParagraphElement>(null);
  const feedback=useRef<HTMLDivElement>(null);
  const heading=useRef<HTMLHeadingElement>(null);
  const npcAudio=useRef<HTMLAudioElement>(null);
  const replyAudio=useRef<HTMLAudioElement>(null);
  const playNext=useRef<'npc'|'reply'|null>(null);
  const turn=saved?.current_turn;
  const accepted=!!turn?.answered && !!turn.feedback?.correct;
  const blockingRetry=retryCommand && !['npc','reply'].includes(retryCommand.kind);
  const disabled=loading || !!busy || !!blockingRetry || needsReload || accountChanged;

  function accept(value:StepConversation,restore=false) {
    if (restore || currentTurn.current!==value.current_turn?.id) {
      setSelected(value.current_turn?.feedback?.option_id ?? '');
      setAudioNotice('');
      playbackRequest.current++;setPlaying(null);
      npcAudio.current?.pause();replyAudio.current?.pause();
    }
    currentTurn.current=value.current_turn?.id;
    setSaved(value);
  }

  function report(reason:unknown) {
    const blocked=reason instanceof ApiError && ['account_changed','profile_changed'].includes(reason.code);
    setAccountChanged(blocked);
    setError(reason instanceof Error ? reason.message : t('The conversation could not be loaded. Please try again.','Не удалось загрузить разговор. Попробуйте ещё раз.'));
    return blocked;
  }

  async function load(id:string|null|undefined=sessionId ?? saved?.id) {
    if (inFlight.current) return;
    const version=generation.current;
    inFlight.current=true;setLoading(true);setError('');setRetryCommand(null);
    try {
      if (id) {
        const value=await api<StepConversation>(`${endpoint}/${encodeURIComponent(id)}`,undefined,controller.current?.signal);
        if (version===generation.current) accept(value,true);
      } else {
        const query=new URLSearchParams({scenario_id:scenarioId ?? 'cafe',level:targetLevel});
        const value=await api<Options>(`${endpoint}/options?${query}`,undefined,controller.current?.signal);
        if (version===generation.current) setOptions(value);
      }
      if (version===generation.current) {setNeedsReload(false);setAccountChanged(false);}
    } catch(reason) {if (version===generation.current && !controller.current?.signal.aborted) report(reason);}
    finally {if (version===generation.current) {inFlight.current=false;setLoading(false);}}
  }

  useEffect(()=>{
    controller.current=new AbortController();generation.current++;inFlight.current=false;
    currentTurn.current=undefined;startKey.current=crypto.randomUUID();
    setSaved(undefined);setOptions(undefined);setSelected('');setBusy(null);setNeedsReload(false);setAccountChanged(false);
    playbackRequest.current++;setPlaying(null);
    void load(sessionId ?? null);
    return ()=>{generation.current++;controller.current?.abort();npcAudio.current?.pause();replyAudio.current?.pause();};
  },[sessionId,scenarioId,scenarioSeed,targetLevel]);

  useEffect(()=>{
    if (saved?.state!=='preparing' || saved.retryable || error) return;
    const abort=new AbortController();const version=generation.current;
    const timer=setTimeout(()=>{
      void api<StepConversation>(`${endpoint}/${encodeURIComponent(saved.id)}`,undefined,abort.signal)
        .then(value=>{if (!abort.signal.aborted && version===generation.current) accept(value);})
        .catch(reason=>{if (!abort.signal.aborted && version===generation.current) report(reason);});
    },1500);
    return ()=>{clearTimeout(timer);abort.abort();};
  },[saved,error]);

  useLayoutEffect(()=>{
    if (focusTarget.current==='feedback') feedback.current?.focus({preventScroll:true});
    if (focusTarget.current==='turn') (saved?.state==='completed' ? heading.current : prompt.current)?.focus({preventScroll:true});
    focusTarget.current=null;
  },[saved]);

  async function play(kind:'npc'|'reply') {
    const version=generation.current;
    const request=++playbackRequest.current;
    const audio=kind==='npc' ? npcAudio.current : replyAudio.current;
    if (!audio) return;
    (kind==='npc' ? replyAudio.current : npcAudio.current)?.pause();
    setAudioNotice('');setPlaying(kind);
    try {await audio.play();}
    catch(reason) {
      if (version!==generation.current || request!==playbackRequest.current) return;
      setPlaying(null);
      setAudioNotice(reason instanceof DOMException && reason.name==='NotAllowedError'
        ? t('Audio is ready. Select Listen to play it.','Аудио готово. Нажмите «Послушать».')
        : t('Audio could not play. Try again.','Не удалось воспроизвести аудио. Попробуйте ещё раз.'));
    }
  }

  useEffect(()=>{
    const kind=playNext.current;
    if (kind && (kind==='npc' ? turn?.npc_audio_url : turn?.reply_audio_url)) {playNext.current=null;void play(kind);}
  },[turn?.npc_audio_url,turn?.reply_audio_url]);

  async function run(command:Command) {
    if (inFlight.current || accountChanged) return;
    const version=generation.current;
    inFlight.current=true;setBusy(command.kind);setError('');setRetryCommand(null);
    try {
      const value=await api<StepConversation>(command.url,command.body,controller.current?.signal);
      if (version!==generation.current || controller.current?.signal.aborted) return;
      focusTarget.current=command.kind==='answer' ? 'feedback' : ['next','start','retry'].includes(command.kind) ? 'turn' : null;
      if (command.kind==='npc' || command.kind==='reply') playNext.current=command.kind;
      accept(value);setNeedsReload(false);
      if (command.kind==='start') window.location.hash=`speaking/step/${encodeURIComponent(value.id)}`;
    } catch(reason) {
      if (version!==generation.current || controller.current?.signal.aborted) return;
      const blocked=report(reason);
      const stale=reason instanceof ApiError && ['stale_turn','conflict','answer_required'].includes(reason.code);
      if (blocked || stale) setNeedsReload(true);
      else setRetryCommand(command);
    } finally {if (version===generation.current) {inFlight.current=false;setBusy(null);}}
  }

  function command(kind:Command['kind'],body:Record<string,unknown>={}) {
    if (!saved || disabled) return;
    const path=kind==='npc' || kind==='reply' ? 'audio' : kind;
    void run({kind,url:`${endpoint}/${encodeURIComponent(saved.id)}/${path}`,body:{...body,...(kind==='retry' ? {} : {turn_id:turn?.id}),...(path==='audio' ? {kind} : {})}});
  }
  function listen(kind:'npc'|'reply') {
    if (playing===kind) {
      playbackRequest.current++;
      (kind==='npc' ? npcAudio.current : replyAudio.current)?.pause();
      setPlaying(null);return;
    }
    if (disabled) return;
    if (kind==='npc' ? turn?.npc_audio_url : turn?.reply_audio_url) void play(kind);
    else command(kind);
  }
  const scenario=saved?.scenario ?? options?.scenario;
  const title=saved?.state==='completed' ? t('Conversation complete','Разговор завершён')
    : scenario ? (language==='ru' ? scenario.title_ru || scenario.title : scenario.title) : t('Step-through conversation','Пошаговый разговор');
  const role=scenario ? (language==='ru' ? scenario.role_ru || scenario.role : scenario.role) : undefined;
  const previous=(saved?.transcript ?? []).filter(line=>saved?.state==='completed' || line.id!==turn?.id);
  const showFeedback=turn?.feedback && (accepted || selected===turn.feedback.option_id);
  const audio=(kind:'npc'|'reply')=>saved?.audio_configured===false && !(kind==='npc' ? turn?.npc_audio_url : turn?.reply_audio_url) ? null : <div class="step-audio">
    <button type="button" class="step-text-button" disabled={disabled && playing!==kind} onClick={()=>listen(kind)} aria-label={playing===kind
      ? kind==='npc' ? t('Pause the other speaker','Приостановить запись собеседника') : t('Pause your reply','Приостановить запись своего ответа')
      : kind==='npc' ? t('Listen to the other speaker','Послушать собеседника') : t('Listen to your reply','Послушать свой ответ')}>
      <span aria-hidden="true">{playing===kind ? 'Ⅱ' : '▷'}</span> {busy===kind ? t('Preparing audio…','Готовим аудио…') : playing===kind ? t('Pause','Пауза') : t('Listen','Послушать')}
    </button>
    {(kind==='npc' ? turn?.npc_audio_url : turn?.reply_audio_url) && <audio key={`${turn?.id}-${kind}`} ref={kind==='npc' ? npcAudio : replyAudio} hidden aria-hidden="true" preload="none" src={(kind==='npc' ? turn?.npc_audio_url : turn?.reply_audio_url) ?? undefined}
      onPause={()=>setPlaying(current=>current===kind ? null : current)} onEnded={()=>setPlaying(current=>current===kind ? null : current)}
      onError={()=>{setPlaying(current=>current===kind ? null : current);setAudioNotice(t('Audio could not play. Try again.','Не удалось воспроизвести аудио. Попробуйте ещё раз.'));}}/>}
  </div>;

  return <section class="page activity-entry step-conversation-page"><div class="activity-entry-content">
    <div class="step-meta"><nav class="step-back" aria-label={t('Speaking','Разговорная практика')}>
      {onBack ? <button class="step-text-button" type="button" onClick={onBack}>← {t('Speaking','Разговорная практика')}</button>
        : <a class="text-link" href="#speaking/step">← {t('Speaking','Разговорная практика')}</a>}
    </nav>
    <p class="step-mode">{t('Step-through','По шагам')} · {saved?.target_level ?? targetLevel}</p></div>
    <ActivityHeader title={title} headingRef={heading} headingTabIndex={-1}/>
    {error && <div class="step-error" role="alert"><p>{error}</p><div class="step-actions">
      {accountChanged ? <button type="button" class="step-text-button" onClick={()=>window.location.reload()}>{t('Reload page','Обновить страницу')}</button>
        : <>{retryCommand && <button type="button" class="step-text-button" disabled={!!busy || loading} onClick={()=>void run(retryCommand)}>{t('Try again','Попробовать ещё раз')}</button>}
          {retryCommand?.kind!=='start' && <button type="button" class="step-text-button" disabled={!!busy || loading} onClick={()=>void load()}>{saved || sessionId ? t('Reload conversation','Обновить разговор') : t('Reload scenario','Обновить ситуацию')}</button>}</>}
    </div></div>}
    {loading && <p role="status">{t('Opening your conversation…','Открываем разговор…')}</p>}
    {!loading && !saved && options && <div class="step-preview">
      <p>{language==='ru' ? scenario?.description_ru || scenario?.description : scenario?.description}</p>
      <p class="step-muted">{t('Choose a reply, check it, then continue. You can say the lines aloud; recording is not needed.','Выберите ответ, проверьте его и продолжайте. Реплики можно произносить вслух — запись не нужна.')}</p>
      {options.configured && options.scenario ? <button type="button" class="cta" disabled={disabled} onClick={()=>void run({kind:'start',url:endpoint,body:{submission_id:startKey.current,scenario_id:scenarioId ?? 'cafe',scenario_seed:scenarioSeed ?? options.scenario?.seed,target_level:targetLevel,language}})}>
        {busy==='start' ? t('Preparing your conversation…','Готовим разговор…') : t('Start step-through','Начать пошаговый разговор')}
      </button> : <p role="status" class="step-muted">{options.configured ? t('No conversation is available for this level yet.','Для этого уровня пока нет подходящего разговора.') : t('Step-through conversations are not available right now.','Пошаговые разговоры сейчас недоступны.')}</p>}
      {!!options.sessions?.length && <details class="step-history"><summary>{t('Previous conversations','Предыдущие разговоры')}</summary><ul class="step-history-links">
        {options.sessions.map(item=><li key={item.id}><a href={`#speaking/step/${encodeURIComponent(item.id)}`}>{language==='ru' ? item.title_ru || item.title : item.title} <span>{item.target_level} · {item.state==='completed' ? t('Complete','Завершён') : t('Continue','Продолжить')}</span></a></li>)}
      </ul></details>}
    </div>}
    {!loading && saved?.state==='preparing' && !saved.retryable && <p role="status">{t('Preparing your conversation…','Готовим разговор…')}</p>}
    {!loading && saved && (saved.state==='failed' || saved.state==='preparing' && saved.retryable) && <div class="step-error"><p role="alert">{saved.error || t('The conversation could not be prepared.','Не удалось подготовить разговор.')}</p>
      {saved.retryable && <button type="button" class="cta" disabled={disabled} onClick={()=>command('retry')}>{busy==='retry' ? t('Preparing…','Готовим…') : t('Try preparing again','Попробовать снова')}</button>}
    </div>}
    {!loading && saved?.state==='active' && turn && <>
      <div class="step-progress"><span>{t(`Step ${turn.ordinal} of ${saved.turn_count}`,`Шаг ${turn.ordinal} из ${saved.turn_count}`)}</span><progress value={saved.completed_turns} max={saved.turn_count} aria-label={t('Conversation progress','Прогресс разговора')}/></div>
      <div class="step-npc"><span class="step-speaker">{role || t('Other speaker','Собеседник')}</span><p ref={prompt} tabIndex={-1} lang="ru">{turn.npc.russian}</p>{audio('npc')}</div>
      {!accepted && <form onSubmit={event=>{event.preventDefault();if (selected && !disabled) command('answer',{submission_id:crypto.randomUUID(),option_id:selected});}}>
        <fieldset disabled={disabled} class="step-choices"><legend>{local(turn.intent)}</legend>
          {turn.options.map(option=><label key={option.id} class={`step-choice${selected===option.id ? ' is-selected' : ''}`}><input type="radio" name={`reply-${turn.id}`} value={option.id} checked={selected===option.id} onChange={()=>{setSelected(option.id);setError('');}}/><span lang="ru">{option.russian}</span></label>)}
        </fieldset>
        <div class="step-hint">{turn.hint ? <p>{local(turn.hint)}</p> : <button type="button" class="step-text-button" disabled={disabled} onClick={()=>command('hint')}>{busy==='hint' ? t('Opening hint…','Открываем подсказку…') : t('Show a hint','Показать подсказку')}</button>}</div>
        {showFeedback && <div class="step-feedback" role="status" ref={feedback} tabIndex={-1}><strong>{t('Try another reply.','Попробуйте другой ответ.')}</strong><p>{local(turn.feedback!.explanation)}</p></div>}
        <button type="submit" class="cta" disabled={!selected || disabled}>{busy==='answer' ? t('Checking…','Проверяем…') : t('Check reply','Проверить ответ')}</button>
      </form>}
      {accepted && <div class="step-feedback is-accepted" role="status" ref={feedback} tabIndex={-1}>
        <span class="step-speaker">{t('Your reply','Ваш ответ')}</span><p class="step-accepted-russian" lang="ru">{turn.options.find(option=>option.id===turn.feedback!.option_id)?.russian}</p><p class="step-translation" lang="en">{turn.feedback!.english}</p>
        <p>{local(turn.feedback!.explanation)}</p>{audio('reply')}
        <button type="button" class="cta" disabled={disabled} onClick={()=>command('next')}>{busy==='next' ? t('Continuing…','Продолжаем…') : t('Continue','Продолжить')}</button>
      </div>}
      {audioNotice && <p class="step-muted" role="status">{audioNotice}</p>}
    </>}
    {!loading && saved?.state==='completed' && <div class="step-complete">
      {saved.ending && <><p class="step-ending" lang="ru">{saved.ending.russian}</p><p class="step-translation" lang="en">{saved.ending.english}</p></>}
      <p>{t(`You worked through ${saved.completed_turns} replies. Your conversation is saved.`,'Вы разобрали все реплики. Разговор сохранён.')}</p>
      {saved.reward && saved.reward.amount>0 && <p class="step-reward">{t(`Lingocoins earned: ${saved.reward.amount}`,`Получено лингокоинов: ${saved.reward.amount}`)}</p>}
      <a class="cta" href="#speaking/step">{t('Choose another conversation','Выбрать другой разговор')}</a>
    </div>}
    {!loading && !!previous.length && <details class="step-history"><summary>{saved?.state==='completed' ? t('Review conversation','Посмотреть разговор') : t('Conversation so far','Предыдущие реплики')}</summary><ol>
      {previous.map(line=><li key={line.id}><p lang="ru"><span class="step-speaker">{role || t('Other speaker','Собеседник')}</span>{line.npc.russian}</p><p lang="ru"><span class="step-speaker">{t('You','Вы')}</span>{line.reply.russian}</p><p class="step-translation" lang="en">{line.reply.english}</p></li>)}
    </ol></details>}
  </div></section>;
}

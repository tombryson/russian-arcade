import { useEffect, useRef, useState } from 'preact/hooks';
import { api } from './learning-api';
import { CardTags, CardMedia, cardLabel } from './CardDetails';
import { Sheet } from './components';
import { nextTime, ratingLabel, words, type CardOverview, type CardScope, type CardHistory, type Language, type LibraryCard, type ReviewSession } from './review-types';

export function Flashcards({ profileId, language = 'en', personal = false, wordId, lessonId, topic }: { profileId: string; language?: Language; personal?: boolean; wordId?: number; lessonId?: string; topic?: string }) {
  const t = words(language);
  const [data, setData] = useState<CardOverview>();
  const [scope, setScope] = useState<CardScope>({...wordId ? {word_id:String(wordId)} : {}, ...lessonId ? {lesson_id:lessonId} : {}, ...topic ? {topic} : {}});
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [mediaCard,setMediaCard] = useState('');
  const [mediaProgress,setMediaProgress] = useState('');
  const [size, setSize] = useState(10);
  const [history, setHistory] = useState<CardHistory>();
  const pending = useRef<object>();
  const working = useRef(false);
  const controller = useRef<AbortController>();
  const heading = useRef<HTMLHeadingElement>(null);
  const query = new URLSearchParams(Object.entries(scope).filter(([,value]) => !!value)).toString();
  useEffect(() => {
    const request = new AbortController(); controller.current = request;
    setError(''); setData(undefined); setHistory(undefined);
    void api<CardOverview>(`/api/v1/flashcards${query ? `?${query}` : ''}`, undefined, request.signal).then(value => {
      if (request.signal.aborted) return;
      if (value.profile_id !== profileId) throw new Error(t('The study profile changed. Reload this page.', 'Профиль изменился. Обновите страницу.'));
      setData(value);
    }).catch(reason => { if (!request.signal.aborted) setError(reason instanceof Error ? reason.message : t('Cards could not open.', 'Не удалось открыть карточки.')); });
    return () => request.abort();
  }, [profileId, query, revision]);
  useEffect(() => { heading.current?.focus(); }, []);

  async function start() {
    if (!data || working.current) return;
    if (data.active_session_id && !pending.current) { window.location.hash = `review/${data.active_session_id}`; return; }
    if (!pending.current) pending.current = { profile_id: profileId, scope, size, submission_id: crypto.randomUUID() };
    const request = controller.current;
    working.current = true; setBusy(true); setError('');
    try {
      const saved = await api<ReviewSession>('/api/v1/review-sessions', pending.current, request?.signal);
      if (request?.signal.aborted) return;
      if (saved.profile_id !== profileId) throw new Error(t('The study profile changed. Reload this page.', 'Профиль изменился. Обновите страницу.'));
      pending.current = undefined; window.location.hash = `review/${saved.id}`;
    } catch (reason) {
      if (!request?.signal.aborted) setError(reason instanceof Error ? reason.message : t('We could not confirm the start. Try again.', 'Не удалось подтвердить начало. Попробуйте ещё раз.'));
    } finally { working.current = false; if (!request?.signal.aborted) setBusy(false); }
  }
  async function suspend(card: LibraryCard) {
    if (working.current || pending.current) return;
    const request = controller.current;
    working.current = true; setBusy(true); setError('');
    try {
      await api(`/api/v1/flashcards/${card.id}/suspension`, { profile_id: profileId, suspended: card.status !== 'suspended', expected_revision: card.revision }, request?.signal);
      if (!request?.signal.aborted) setRevision(v => v + 1);
    } catch (reason) { if (!request?.signal.aborted) setError(reason instanceof Error ? reason.message : t('Reload the library to check this card.', 'Обновите коллекцию и проверьте карточку.')); }
    finally { working.current = false; if (!request?.signal.aborted) setBusy(false); }
  }
  async function deleteCard(card: LibraryCard) {
    if (working.current || pending.current) return;
    working.current=true;setBusy(true);setError('');
    try {
      await api(`/api/v1/cards/${card.id}/delete`,{},controller.current?.signal);
      if (!controller.current?.signal.aborted) setRevision(v => v+1);
    } catch (reason) { if (!controller.current?.signal.aborted) setError(reason instanceof Error ? reason.message : 'Could not delete the card.'); }
    finally { working.current=false;setBusy(false); }
  }
  async function addMedia(card: LibraryCard) {
    if (working.current) return;
    const request=controller.current;
    working.current=true;setBusy(true);setError('');setMediaCard(card.id);setMediaProgress(t('Creating media…','Создаём файлы…'));
    try {
      let retry=true;
      while (!request?.signal.aborted) {
        const result=await api<{ complete: boolean; saved: number; failed: number }>(`/api/v1/flashcards/${card.id}/media`,retry ? {retry:true} : {},request?.signal);
        retry=false;
        if (request?.signal.aborted) return;
        setMediaProgress(`${result.saved} / 3 ${t('saved','сохранено')}`);
        if (result.complete) {
          if (result.failed) setError(t('The card is saved, but some media could not be created. Use Retry media to try again.','Карточка сохранена, но часть файлов не создана. Нажмите «Повторить создание файлов».'));
          const value=await api<CardOverview>(`/api/v1/flashcards${query ? `?${query}` : ''}`,undefined,request?.signal);
          if (!request?.signal.aborted && value.profile_id===profileId) setData(value);
          break;
        }
        await new Promise(resolve => window.setTimeout(resolve,1000));
      }
    } catch (reason) { if (!request?.signal.aborted) setError(reason instanceof Error ? reason.message : 'Media creation paused.'); }
    finally { working.current=false;setBusy(false);setMediaCard('');setMediaProgress(''); }
  }
  async function inspectHistory(card: LibraryCard) {
    const request = controller.current;
    try {
      const value = await api<CardHistory>(`/api/v1/flashcards/${card.id}/history`, undefined, request?.signal);
      if (value.profile_id !== profileId) throw new Error(t('The study profile changed. Reload this page.', 'Профиль изменился. Обновите страницу.'));
      if (!request?.signal.aborted) setHistory(value);
    } catch (reason) { if (!request?.signal.aborted) setError(reason instanceof Error ? reason.message : t('History could not open.', 'Не удалось открыть историю.')); }
  }
  const label = (value: string) => ({ new: t('New', 'Новая'), learning: t('Learning', 'Изучаю'), reviewing: t('Reviewing', 'Повторяю'), suspended: t('Set aside', 'Отложена') })[value] ?? value;
  const decks = data?.facets?.decks ?? Array.from(new Map(data?.cards.flatMap(c => c.decks).map(d => [d.content_id, d])).values());
  return <section class="page flashcards-page">
    <header class="flashcards-heading"><div><p class="kicker">{t('Study', 'Учить')}</p><h1 ref={heading} tabIndex={-1}>{t('Flashcards', 'Карточки')}</h1></div>
      {personal && <a class="cta" href={data?.lesson?.url ?? (scope.word_id ? `#generate?word_id=${scope.word_id}` : '#generate')}>{t('Generate cards','Создать карточки')} <span aria-hidden="true">＋</span></a>}
      <p class="intro">{t('Study your vocabulary and pick up where you left off.', 'Учите слова и продолжайте с того места, где остановились.')}</p>
    </header>
    {data?.lesson && <div class="letter lesson-card-context"><strong>{data.lesson.title}</strong><div class="action-row"><a class="text-link" href={data.lesson.url}>{t("Back to lesson", "К уроку")} →</a><a class="text-link" href="#flashcards">{t("All flashcards", "Все карточки")}</a></div></div>}
    {scope.word_id && <p class="intro">{t('Showing cards for this vocabulary word.', 'Карточки выбранного слова.')} <button class="text-link" disabled={busy || !!pending.current} onClick={() => setScope(lessonId ? {lesson_id:lessonId} : {})}>{t('Show all cards', 'Показать все карточки')}</button></p>}
    {error && <div class="error-note" role="alert"><p>{error}</p><div class="action-row"><button class="text-link" onClick={() => { pending.current = undefined; setRevision(v => v + 1); }}>{t('Reload cards', 'Обновить карточки')}</button>{!personal && <a href="/post/household">{t('Choose a learner', 'Выбрать ученика')}</a>}</div></div>}
    {!data ? !error && <p role="status">{t('Opening your cards…', 'Открываем карточки…')}</p> : <>
      <div class="review-welcome"><div class="review-invitation"><span class="card-stack-mark" aria-hidden="true">Я<br /><span>↻</span></span><div class="review-invitation-copy"><div class="review-invitation-message"><p class="kicker">{data.active_session_id ? t('Pick up where you left off', 'Продолжим с того же места') : t('Your next practice', 'Следующая практика')}</p><h2>{data.active_session_id ? t('Your cards are waiting.', 'Карточки вас ждут.') : data.counts.ready ? data.counts.due ? t('Let’s revisit a few words.', 'Давайте повторим несколько слов.') : t('Start with a few words.', 'Начнём с нескольких слов.') : data.counts.media_pending ? t('Finishing your cards’ pictures and audio.','Готовим картинки и аудио.') : data.counts.cards ? t('A good moment for a break.', 'Можно немного отдохнуть.') : personal ? t('No flashcards yet.', 'Пока нет карточек.') : t('Choose your first cards together.', 'Выберите первые карточки вместе.')}</h2>
        {data.counts.cards ? <p>{`${t('Ready to revisit', 'Готовы к повторению')}: ${data.counts.due} · ${t('New today, up to', 'Новых сегодня, до')}: ${Math.min(data.counts.new, data.counts.new_allowance)}`}</p> : !personal && <p>{t('A grown-up can prepare and approve a few cards from your vocabulary.', 'Взрослый может подготовить и одобрить несколько карточек из вашего словаря.')}</p>}
        </div>
        {data.active_session_id || data.counts.ready ? <button class="cta" disabled={busy} onClick={() => void start()}>{busy ? t('Opening…', 'Открываем…') : pending.current ? t('Try starting again', 'Попробовать начать снова') : data.active_session_id ? t('Continue practice', 'Продолжить') : t('Start practice', 'Начать практику')} <span aria-hidden="true">→</span></button>
          : data.counts.cards ? <p class="quiet">{data.counts.next_due_at ? `${t('Next review', 'Следующее повторение')}: ${nextTime(data.counts.next_due_at, data.server_now, language)}.` : data.counts.suspended ? t('Some cards are set aside. You can restore them in your collection.', 'Некоторые карточки отложены. Их можно вернуть в коллекции.') : t('You can browse your cards, change the selection or return tomorrow.', 'Можно посмотреть карточки, изменить выбор или вернуться завтра.')}</p> : <a class="cta" href={personal ? '#generate' : '/post/household'}>{personal ? t('Generate my first cards','Создать первые карточки') : t('Choose cards with a grown-up', 'Выбрать карточки со взрослым')}</a>}
      </div></div><dl class="review-today"><div><dt>{t('Cards practised today', 'Карточек за сегодня')}</dt><dd>{data.counts.practised_today}</dd></div><div><dt>{t('Words in this collection', 'Слов в коллекции')}</dt><dd>{data.counts.words}</dd></div></dl></div>
      <details class="review-options"><summary>{t('Choose cards & session size', 'Выбрать карточки и длину занятия')}</summary><form key={query} class="review-filters" onSubmit={event => { event.preventDefault(); if (pending.current || busy) return; const form = new FormData(event.currentTarget); setScope(Object.fromEntries([...form.entries()].map(([k,v]) => [k,String(v)]))); }}>
        {data?.lesson && <div class="letter lesson-card-context"><strong>{data.lesson.title}</strong><div class="action-row"><a class="text-link" href={data.lesson.url}>{t("Back to lesson", "К уроку")} →</a><a class="text-link" href="#flashcards">{t("All flashcards", "Все карточки")}</a></div></div>}
    {scope.lesson_id && <input type="hidden" name="lesson_id" value={scope.lesson_id} />}{scope.word_id && <input type="hidden" name="word_id" value={scope.word_id} />}
        <label>{t('Search cards', 'Найти карточки')}<input name="q" value={scope.q} maxLength={120} /></label>
        <label>{t('Collection', 'Коллекция')}<select name="deck" value={scope.deck ?? ''}><option value="">{t('All cards', 'Все карточки')}</option>{decks.map(d => <option key={d.content_id} value={d.content_id}>{language==='ru' && d.title_ru ? d.title_ru : d.title}</option>)}{scope.deck && !decks.some(d => d.content_id===scope.deck) && <option value={scope.deck}>{t('Selected collection', 'Выбранная коллекция')}</option>}</select></label>
        {!!data.facets?.topics.length && <label>{t('Topic', 'Тема')}<select name="topic" value={scope.topic ?? ''}><option value="">{t('All topics', 'Все темы')}</option>{data.facets.topics.map(topic => <option key={topic} value={topic}>{cardLabel(topic,language)}</option>)}</select></label>}
        <label>{t('Practise', 'Что практикуем')}<select name="direction" value={scope.direction ?? ''}><option value="">{t('All types', 'Все виды')}</option><option value="ru-en">{t('Russian → English', 'Русский → Английский')}</option><option value="en-ru">{t('English → Russian', 'Английский → Русский')}</option><option value="ru-cloze">{t('Missing word', 'Пропущенное слово')}</option></select></label>
        <label>{t('Word type','Часть речи')}<select name="pos" value={scope.pos ?? ''}><option value="">{t('All word types','Все части речи')}</option>{data.facets?.pos?.map(value => <option value={value}>{cardLabel(value,language)}</option>)}</select></label>
        <label>{t('Case','Падеж')}<select name="case" value={scope.case ?? ''}><option value="">{t('All cases','Все падежи')}</option>{data.facets?.cases?.map(value => <option value={value}>{cardLabel(value,language)}</option>)}</select></label>
        <label>{t('Difficulty','Сложность')}<select name="difficulty" value={scope.difficulty ?? ''}><option value="">{t('Any difficulty','Любая сложность')}</option>{[1,2,3,4,5,6,7,8].map(value => <option value={value}>{value}/8</option>)}</select></label>
        <label>{t('Sort collection','Порядок карточек')}<select name="sort" value={scope.sort ?? 'due'}><option value="due">{t('Due first','Сначала к повторению')}</option><option value="alphabetical">{t('Russian A–Я','По алфавиту')}</option><option value="difficulty">{t('Easiest first','Сначала простые')}</option></select></label>
        <label>{t('Show', 'Показать')}<select name="state" value={scope.state ?? ''}><option value="">{t('All states', 'Все состояния')}</option><option value="due">{t('Ready now', 'Пора повторить')}</option>{['new','learning','reviewing','suspended'].map(s => <option key={s} value={s}>{label(s)}</option>)}</select></label>
        <div class="action-row"><button class="cta" disabled={busy || !!pending.current}>{t('Apply selection', 'Применить')}</button><button type="button" class="text-link" disabled={busy || !!pending.current} onClick={() => setScope(lessonId ? {lesson_id:lessonId} : {})}>{t('Reset selection', 'Сбросить выбор')}</button></div></form>
        <label class="session-size">{t('Cards per short session', 'Карточек за занятие')}<select value={size} disabled={busy || !!pending.current} onChange={e => setSize(Number(e.currentTarget.value))}>{[5,10,20].map(n => <option value={n} key={n}>{n}</option>)}</select></label><p class="quiet">{t('Up to five new cards each day. Related cards are spaced apart; your session may contain fewer cards. Changing this selection does not move due dates.', 'До пяти новых карточек в день. Связанные карточки разнесены по времени, поэтому занятие может быть короче. Изменение выбора не меняет сроки повторения.')}</p>
      </details>
      <details class="native-library" open={!!scope.word_id || !!scope.lesson_id}><summary>{t('Browse your cards', 'Посмотреть карточки')} <span class="quiet">· {data.counts.cards}</span></summary><p>{t('Browsing does not record an answer or change a schedule.', 'Просмотр не записывает ответ и не меняет расписание.')}</p>
        <div class="native-library-grid">{data.cards.map(card => <article class="native-library-card" key={card.id}><div class="card-type-line"><span>{card.media_ready===false ? t('Media needed','Нужны картинка и аудио') : card.buried ? t('Spaced for later', 'На потом') : card.due ? t('Ready now', 'Пора повторить') : label(card.status)}</span><span>{card.direction === 'ru-cloze' ? t('Missing word', 'Пропуск') : card.direction === 'en-ru' ? t('Russian recall', 'По-русски') : t('Meaning', 'Значение')}</span></div><h3>{language === 'ru' && card.title_ru ? card.title_ru : card.title}</h3><p class="library-prompt" lang={card.direction === 'en-ru' ? 'en' : 'ru'}>{card.prompt.replace('[[blank]]','[...]')}</p>{card.direction==='ru-cloze' && card.cue_en && <p class="recall-word-meaning" lang="en">{card.cue_en}</p>}<details><summary>{t('Look at the answer', 'Посмотреть ответ')}</summary><p class="prepared-answer">{card.dictionary_url && card.direction!=='ru-en' ? <a href={card.dictionary_url} target="_blank" rel="noopener noreferrer">{card.answer}</a> : card.answer}</p>{card.assets?.map(asset => <CardMedia key={`${asset.kind ?? "asset"}:${asset.id}`} asset={asset} language={language} />)}<p lang="ru">{card.context}</p>{card.context_meaning && <p>{card.context_meaning}</p>}<p>{language === 'ru' && card.explanation_ru ? card.explanation_ru : card.explanation}</p></details>
          {card.sources?.map(source => <a class="text-link" href={source.url}>{source.origin==='example' ? t("New example · ","Новый пример · ") : ""}{source.title} · {t("Page","Страница")} {source.page}</a>)}
          <CardTags metadata={card.metadata} language={language} /><div class="library-actions"><button class="text-link" disabled={busy || !!pending.current} onClick={() => void suspend(card)}>{card.status === 'suspended' ? t('Return to practice', 'Вернуть в практику') : t('Set aside', 'Отложить')}</button><button class="text-link" onClick={() => void inspectHistory(card)}>{t('History', 'История')}</button></div>
          {personal && card.media_supported!==false && !['image','word_audio','sentence_audio'].every(kind => card.assets?.some(a => a.kind===kind)) && <div class="library-actions"><button class="text-link" disabled={busy} onClick={() => void addMedia(card)}>{mediaCard===card.id ? mediaProgress : card.media_jobs?.some(j => j.status==='failed') ? t('Retry media','Повторить создание файлов') : card.media_jobs?.length ? t('Resume media','Продолжить создание файлов') : t('Add audio & picture','Добавить аудио и картинку')}</button></div>}
          {personal && <div class="library-actions"><a class="text-link" href={`/post/flashcards/manage?edit=${card.version_id}`}>{t('Edit card','Изменить')}</a><button class="text-link" disabled={busy} onClick={() => void deleteCard(card)}>{t('Delete card','Удалить')}</button></div>}
          {history?.card_id === card.id && <div class="card-history" aria-live="polite">{history.events.length ? <ol>{history.events.map((event,index) => <li key={index}><time>{new Date(event.at*1000).toLocaleString(language)}</time> · {ratingLabel(event.rating,language)}{event.assisted ? t(' · with help', ' · с помощью') : ''}{event.undone ? t(' · undone', ' · отменено') : ''}</li>)}</ol> : <p>{t('No reviews yet.', 'Повторений пока нет.')}</p>}</div>}
        </article>)}</div>{!data.cards.length && <p>{t('No cards match this selection.', 'Нет карточек с такими условиями.')}</p>}
      </details>
    </>}
  </section>;
}

export function FlashcardsSetup({ adult, language='en' }: { adult: boolean; language?: Language }) {
  const t=words(language);
  return <section class="page"><p class="kicker">{t('Flashcards', 'Карточки')}</p><h1>{t('Set up flashcard practice.', 'Настроим практику с карточками.')}</h1><Sheet><h2>{t('One learner. Their own practice.', 'У каждого своя практика.')}</h2><p>{t('Choose a learner to save their cards and review schedule. A grown-up can prepare cards, explain tricky meanings and approve them before practice.', 'Выберите ученика, чтобы сохранять его карточки и расписание. Взрослый может подготовить карточки, объяснить сложные значения и одобрить материал.')}</p><div class="action-row"><a class="cta" href="/post/household">{t('Choose a learner', 'Выбрать ученика')}</a>{adult && <a class="text-link" href="/post/flashcards/manage">{t('Prepare & review cards', 'Подготовить и проверить карточки')}</a>}</div></Sheet></section>;
}

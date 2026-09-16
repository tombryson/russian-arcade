(() => {
  'use strict';
  const badges=()=>document.querySelectorAll('[data-progression-badge]');
  if (!badges().length) return;
  const originalFetch=window.fetch;
  let busy=false,queued=false,timer,lastData;
  const railStates=new WeakMap();
  function renderSkill(data,error=false) {
    document.querySelectorAll('[data-skill-rail]').forEach(rail=>{
      const t=(en,ru)=>rail.dataset.language==='ru' ? ru : en;
      const number=value=>Math.round(value).toLocaleString(rail.dataset.language==='ru' ? 'ru-RU' : 'en-AU');
      const skill=data?.skill;
      const candidate=skill?.skills?.find(item=>item.id===skill.active_skill);
      const active=candidate && Number.isFinite(candidate.rating) && candidate.observations>0 ? candidate : null;
      const progress=active && Number.isFinite(active.progress) ? Math.max(0,Math.min(1,active.progress)) : 0;
      const previous=railStates.get(rail);
      const key=active ? `${data.profile_id}:${skill.policy_version}:${active.id}` : '';
      const moving=!!(active && previous?.key===key && active.rating>previous.rating && active.stage===previous.stage);
      if (previous?.timer) clearTimeout(previous.timer);
      rail.classList.toggle('is-moving',moving);
      rail.classList.toggle('is-unavailable',!data);
      rail.style.setProperty('--skill-progress',String(progress));
      const rating=active ? `${t(active.label,active.label_ru)} · ${t('Stage','Этап')} ${active.stage}. ${number(active.rating)} ${t('provisional Elo; next stage at','— предварительный рейтинг Эло; следующий этап —')} ${number(active.stage_end)}` : data ? t('Skill progress has no checked activities yet','Пока нет проверенных заданий для оценки навыков') : t('Skill progress unavailable','Прогресс навыков недоступен');
      const stale=data && error ? t(' Showing your last saved progress.',' Показан последний сохранённый прогресс.') : '';
      rail.querySelector('.skill-rail-link').setAttribute('aria-label',`${rating}.${stale} ${t('View your profile and skill progress','Открыть профиль и прогресс навыков')}`);
      rail.querySelector('.skill-rail-runner').hidden=!data;
      const bar=rail.querySelector('[data-skill-bar]');
      bar.hidden=!active;
      if (active) {bar.setAttribute('aria-valuenow',String(Math.round(progress*100)));bar.setAttribute('aria-valuetext',`${number(active.rating)} ${t('Elo; next stage at','Эло; следующий этап —')} ${number(active.stage_end)}`);}
      else {bar.removeAttribute('aria-valuenow');bar.removeAttribute('aria-valuetext');}
      railStates.set(rail,{key,rating:active?.rating,stage:active?.stage,timer:moving ? setTimeout(()=>rail.classList.remove('is-moving'),800) : null});
    });
  }
  async function refresh() {
    if (busy) {queued=true;return;}
    busy=true;
    try {
      const response=await originalFetch.call(window,'/api/v1/progression',{credentials:'same-origin',cache:'no-store',headers:{Accept:'application/json'}});
      if (response.status===401 || response.status===403) lastData=undefined;
      const data=await response.json();
      if (data.error?.code==='profile_changed') lastData=undefined;
      if (!response.ok) throw new Error('Progress unavailable');
      if (!Number.isFinite(data.balance)) throw new Error('Progress unavailable');
      lastData=data;
      badges().forEach(badge=>{
        const number=badge.querySelector('[data-progression-balance]');
        if (number) number.textContent=String(data.balance);
        badge.setAttribute('aria-label',`${badge.dataset.language==='ru' ? 'Лингокоины' : 'Lingo coins'}: ${data.balance}`);
      });
      renderSkill(data);
    } catch (_) {
      renderSkill(lastData,true);
      if (!lastData) badges().forEach(badge=>{badge.querySelector('[data-progression-balance]').textContent='—';badge.setAttribute('aria-label',badge.dataset.language==='ru' ? 'Лингокоины: недоступно' : 'Lingo coins: unavailable');});
    } finally {busy=false;if (queued) {queued=false;schedule();}}
  }
  function schedule() {clearTimeout(timer);timer=setTimeout(refresh,350);}
  window.addEventListener('lingo:progression',schedule);
  document.addEventListener('visibilitychange',()=>{if (document.visibilityState==='visible') schedule();});
  document.addEventListener('htmx:afterRequest',schedule);
  document.addEventListener('submit',()=>{setTimeout(schedule,1200);},true);
  const header=document.querySelector('.arcade-header');
  if (header) {
    const measure=()=>{const height=`${header.getBoundingClientRect().height}px`;document.documentElement.style.setProperty('--arcade-header-height',height);document.documentElement.style.setProperty('--skill-header-height',height);};
    measure();
    if (typeof ResizeObserver!=='undefined') new ResizeObserver(measure).observe(header);
    else window.addEventListener('resize',measure);
  }
  // Existing activities use both fetch and HTMX. Refresh only header progress
  // after same-origin writes, preserving the response and the activity draft.
  window.fetch=function(input,options) {
    const result=originalFetch.apply(this,arguments);
    try {
      const request=input instanceof Request ? input : null;
      const url=new URL(request ? request.url : String(input),window.location.href);
      const method=(options?.method || request?.method || 'GET').toUpperCase();
      if (url.origin===window.location.origin && method!=='GET' && method!=='HEAD' && !/\/(?:heartbeat|connect)$/.test(url.pathname)) {
        void result.then(response=>{if (response.ok) schedule();}).catch(()=>{});
      }
    } catch (_) { /* Leave unfamiliar request objects untouched. */ }
    return result;
  };
  setInterval(()=>{if (document.visibilityState==='visible') void refresh();},30000);
  void refresh();
})();

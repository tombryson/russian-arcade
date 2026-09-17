import { useLayoutEffect, useRef, useState } from 'preact/hooks';
import type { Language } from './review-types';
import type { ProgressionData, ProgressionState } from './Progression';
import '../../static/css/skill_progress.css';

export type SkillRating={id:string;label:string;label_ru:string;status:string;rating:number|null;stage:number;stage_start:number;stage_end:number;progress:number;observations:number;last_updated:number|null;points_to_next:number};
export type SkillProgressData={status:string;policy_version?:string;active_skill?:string;skills?:SkillRating[]};
export function activeRating(data?:ProgressionData):SkillRating|undefined {
  const item=data?.skill.skills?.find(skill=>skill.id===data.skill.active_skill);
  return item && Number.isFinite(item.rating) && item.observations>0 ? item : undefined;
}
export const boundedProgress=(value?:number)=>Number.isFinite(value) ? Math.min(1,Math.max(0,value!)) : 0;

export function SkillProgress({progression,language='en',introductory=false,profileHref='/post/profiles#skill-progress'}:{progression:ProgressionState;language?:Language;introductory?:boolean;profileHref?:string}) {
  const t=(en:string,ru:string)=>language==='ru' ? ru : en;
  const number=(value:number)=>Math.round(value).toLocaleString(language==='ru' ? 'ru-RU' : 'en-AU');
  const previous=useRef<{key:string;rating:number|null;stage:number}>();
  const [moving,setMoving]=useState(false);
  const data=introductory ? undefined : progression.data;
  const active=activeRating(data);
  // A visual-only preview: the actual progression data stays untouched.
  const preview=new URLSearchParams(window.location.search).get('progress-preview')==='50';
  const progress=preview ? .5 : boundedProgress(active?.progress);
  const unavailable=!data && !introductory && !!progression.error;
  const label=preview ? t('50% layout preview; saved progress unchanged','Предпросмотр 50%; сохранённый прогресс не изменён') : active ? `${t(active.label,active.label_ru)} · ${t('Stage','Этап')} ${active.stage} · ${number(active.rating!)} ${t('provisional Elo','предварительный рейтинг Эло')}` : unavailable ? t('Skill progress unavailable','Прогресс навыков недоступен') : !data && !introductory ? t('Loading skill progress…','Загружаем прогресс навыков…') : '';
  const linkLabel=[label,t('View skill progress in your profile','Посмотреть прогресс навыков в профиле')].filter(Boolean).join('. ');
  useLayoutEffect(()=>{
    const key=data ? `${data.profile_id}:${data.skill.policy_version}:${active?.id ?? data.skill.active_skill ?? 'reading'}` : '';
    const last=previous.current;
    const increased=active && last && (last.rating===null ? active.progress>0 : active.rating!>last.rating);
    const shouldMove=!!(!preview && increased && active && last && last.key===key && active.stage===last.stage);
    // Remember the same profile's empty starting line so its first real result
    // can move Barsik, without animating saved ratings on load or profile switch.
    previous.current=data ? {key,rating:active?.rating ?? null,stage:active?.stage ?? 1} : undefined;
    setMoving(shouldMove);
    if (shouldMove) {const timer=setTimeout(()=>setMoving(false),800);return ()=>clearTimeout(timer);}
  },[preview,data?.profile_id,data?.skill.policy_version,active?.id,active?.rating,active?.stage]);
  return <div class={`skill-rail${moving ? ' is-moving' : ''}${!data && !preview && !introductory ? ' is-unavailable' : ''}`} style={{'--skill-progress':progress}}>
    <a class="skill-rail-link" href={profileHref} aria-label={linkLabel}>
      <span class="skill-rail-track" aria-hidden="true"><span class="skill-rail-fill" /></span>
      {(data || preview || introductory) && <span class="skill-rail-runner" aria-hidden="true"><img src="/static/images/barsik-progress-run-v1.webp" alt="" width="56" height="40" /></span>}
      {(active || preview) && <span class="sr-only" role="progressbar" aria-label={t('Progress through this skill stage','Прогресс на этом этапе навыка')} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress*100)} aria-valuetext={preview ? t('50% layout preview; saved progress unchanged','Предпросмотр 50%; сохранённый прогресс не изменён') : `${number(active!.rating!)} ${t('Elo; next stage at','Эло; следующий этап —')} ${number(active!.stage_end)}`} />}
    </a>
  </div>;
}

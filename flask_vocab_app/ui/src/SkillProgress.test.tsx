import { afterEach,describe,expect,it,vi } from 'vitest';
import { render,screen } from '@testing-library/preact';
import { SkillProgress,type SkillRating } from './SkillProgress';
import { useProgression,type ProgressionData } from './Progression';

const skill=(overrides:Partial<SkillRating>={}):SkillRating=>({id:'reading',label:'Reading',label_ru:'Чтение',status:'provisional',rating:1040,stage:1,stage_start:1000,stage_end:1200,progress:.2,observations:3,last_updated:1720000000,points_to_next:160,...overrides});
const data=(rating=skill(),profile='personal',policy='practice-elo-v1'):ProgressionData=>({profile_id:profile,balance:42,earned_total:3,legacy_balance:39,preferred_level:'A1',levels:[],policy:{activity_coins:3,activity_daily_cap:12,review_coins:1,review_daily_cap:10},recent_rewards:[],journey:{worlds:[],next_world:null},skill:{status:'provisional',policy_version:policy,active_skill:rating.id,skills:[rating]}});
const source=(value:ProgressionData|undefined=data(),error='')=>({data:value,error,loading:false,refresh:vi.fn()});
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals();});

describe('Header skill progress',()=>{
  it('links to the profile while keeping the header free of visible labels and popups',()=>{
    const {container}=render(<><input aria-label="Draft" value="Мой ответ" /><SkillProgress progression={source()} /></>);
    const link=screen.getByRole('link',{name:/Reading · Stage 1 · 1,040 provisional Elo/});
    expect(link.getAttribute('href')).toBe('/post/profiles#skill-progress');
    expect(container.querySelector('.skill-rail')?.textContent).toBe('');
    expect(container.querySelector('details')).toBeNull();
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('20');
    expect(screen.getByRole('progressbar').getAttribute('aria-valuetext')).toBe('1,040 Elo; next stage at 1,200');
    expect((screen.getByLabelText('Draft') as HTMLInputElement).value).toBe('Мой ответ');
  });
  it('keeps Barsik at the start without presenting an unmeasured rating or introductory card',()=>{
    const unobserved=skill({rating:null,status:'not_calibrated',progress:0,observations:0});
    const {container}=render(<SkillProgress progression={source(data(unobserved))} />);
    expect(screen.getByRole('link',{name:'View skill progress in your profile'})).toBeTruthy();
    expect(screen.queryByRole('progressbar')).toBeNull();
    expect(container.innerHTML).not.toMatch(/Getting started|1,000|Your first checked activity/);
    expect(container.querySelector('.skill-rail-runner')).toBeTruthy();
  });
  it('keeps loading and unavailable states accessible without showing a false rating',()=>{
    const retry=vi.fn();
    const {container,rerender}=render(<SkillProgress progression={{data:undefined,error:'',loading:true,refresh:retry}} />);
    expect(screen.getByRole('link',{name:/Loading skill progress/})).toBeTruthy();
    expect(container.querySelector('.skill-rail-runner')).toBeNull();
    rerender(<SkillProgress progression={{data:undefined,error:'Unavailable',loading:false,refresh:retry}} />);
    expect(screen.getByRole('link',{name:/Skill progress unavailable/}).getAttribute('href')).toBe('/post/profiles#skill-progress');
    expect(screen.queryByRole('progressbar')).toBeNull();
    expect(container.textContent).toBe('');
  });
  it('moves briefly only for increased rating in the same profile, skill, policy and stage',()=>{
    vi.useFakeTimers();
    const {container,rerender}=render(<SkillProgress progression={source()} />);
    const rail=()=>container.querySelector('.skill-rail') as HTMLElement;
    expect(rail().classList.contains('is-moving')).toBe(false);
    rerender(<SkillProgress progression={source(data(skill({rating:1050,progress:.25})))} />);
    expect(rail().classList.contains('is-moving')).toBe(true);
    // Refreshing the same score must not start another run.
    rerender(<SkillProgress progression={source(data(skill({rating:1050,progress:.25})))} />);
    expect(rail().style.getPropertyValue('--skill-progress')).toBe('0.25');
    vi.advanceTimersByTime(900);
    rerender(<SkillProgress progression={source(data(skill({rating:1030,progress:.15})))} />);
    expect(rail().classList.contains('is-moving')).toBe(false);
    rerender(<SkillProgress progression={source(data(skill({rating:1150,progress:.75}),'another-profile'))} />);
    expect(rail().classList.contains('is-moving')).toBe(false);
    rerender(<SkillProgress progression={source(data(skill({id:'writing',label:'Writing',rating:1190,progress:.95}),'another-profile'))} />);
    expect(rail().classList.contains('is-moving')).toBe(false);
    rerender(<SkillProgress progression={source(data(skill({id:'writing',label:'Writing',rating:1199,progress:.995}),'another-profile','next-policy'))} />);
    expect(rail().classList.contains('is-moving')).toBe(false);
    rerender(<SkillProgress progression={source(data(skill({id:'writing',label:'Writing',rating:1205,stage:2,progress:.025}),'another-profile','next-policy'))} />);
    expect(rail().classList.contains('is-moving')).toBe(false);
  });
  it('moves from the empty starting line on the same learner’s first positive result, but not on load',()=>{
    vi.useFakeTimers();
    const unobserved=skill({rating:null,progress:0,observations:0});
    const first=skill({rating:1012,progress:.06,observations:1});
    const {container,rerender}=render(<SkillProgress progression={source(data(unobserved))} />);
    const rail=()=>container.querySelector('.skill-rail')!;
    rerender(<SkillProgress progression={source(data(first))} />);
    expect(rail().classList.contains('is-moving')).toBe(true);
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('6');
    vi.advanceTimersByTime(900);
    rerender(<SkillProgress progression={source(data(first))} />);
    expect(rail().classList.contains('is-moving')).toBe(false);
    rerender(<SkillProgress progression={source(data(unobserved,'other'))} />);
    rerender(<SkillProgress progression={source(data(first))} />);
    expect(rail().classList.contains('is-moving')).toBe(false);
  });
  it('bounds malformed progress and retains the last saved rating after a failed refresh',()=>{
    const {container,rerender}=render(<SkillProgress progression={source(data(skill({progress:1.3})),'Offline')} />);
    expect((container.querySelector('.skill-rail') as HTMLElement).style.getPropertyValue('--skill-progress')).toBe('1');
    expect(screen.getByRole('link',{name:/1,040 provisional Elo/})).toBeTruthy();
    rerender(<SkillProgress progression={source(data(skill({progress:-.2})))} />);
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('0');
  });
  it.each(['locked','profile_changed'])('clears the previous profile rating after %s instead of showing it as stale',async(code)=>{
    let expired=false;
    vi.stubGlobal('fetch',vi.fn(async()=>expired ? {ok:false,json:async()=>({error:{code,message:'Session changed'}})} : {ok:true,json:async()=>data()}));
    function Header(){return <SkillProgress progression={useProgression(true,'personal')} />;}
    const {container}=render(<Header />);
    await screen.findByRole('link',{name:/Reading · Stage 1/});
    expired=true;window.dispatchEvent(new Event('lingo:progression'));
    await screen.findByRole('link',{name:/Skill progress unavailable/});
    expect(container.querySelector('.skill-rail-runner')).toBeNull();
    expect(screen.queryByRole('progressbar')).toBeNull();
    expect(container.textContent).not.toContain('1,040');
  });
  it('uses Russian accessible labels and the optional household profile route',()=>{
    render(<SkillProgress language="ru" progression={source()} profileHref="/post/household#skill-progress" />);
    expect(screen.getByRole('link',{name:/Чтение · Этап 1.*Посмотреть прогресс навыков в профиле/}).getAttribute('href')).toBe('/post/household#skill-progress');
  });
});

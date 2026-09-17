import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {fireEvent, render, screen} from '@testing-library/preact';
import {JourneyGame} from './JourneyGames';
import {SceneBuilder} from './SceneBuilder';
import {GameLanguage} from './GameLocale';
import type {GameRound, GameState} from './journey-games-api';

const round:GameRound={id:'under-table',mechanic:'scene-builder',objective:'grammar',prompt:'Complete the Russian sentence to describe the scene.',clues:[],max_choices:2,scene_builder:{family:'location',scenario:'Barsik is sitting under the table.',scenario_ru:'Барсик прячется внизу, под столом.',scene:'cat-under-table',segments:['Барсик сидит ',' ','.'],slots:[{id:'preposition',label:'Choose the preposition',label_ru:'Выберите предлог',choices:[{id:'preposition:on',text:'на'},{id:'preposition:under',text:'под'},{id:'preposition:behind',text:'за'}]},{id:'noun',label:'Choose the ending',label_ru:'Выберите окончание',choices:[{id:'noun:nominative',text:'стол'},{id:'noun:prepositional',text:'столе'},{id:'noun:instrumental',text:'столом'}]}]}};
const initial=():GameState=>({id:'scene-test',profile_id:'me',game_id:'scene-builder',title:'Describe the scene',phase:'play',round_index:0,total_rounds:5,round:structuredClone(round),result:null,reward:null,source:{kind:'grammar',title:'Russian grammar',href:'#games/scene-builder'}});
const response=(value:unknown,ok=true)=>({ok,json:async()=>structuredClone(value)});
function service() {
  const model={state:initial(),failAnswer:false};
  const fetch=vi.fn(async(url:string,request?:RequestInit)=>{
    if(url==='/api/v1/games')return response({profile_id:'me',games:[{id:'scene-builder',title:'Describe the scene',description:'Build the sentence.',lesson_id:'bag',lesson_title:'What’s in the bag?',lesson_href:'#first-steps/bag',unlocked:true,new:true,active_session_id:null}]});
    if(request?.method==='GET')return response(model.state);
    const body=JSON.parse(request?.body as string);
    if(url.endsWith('/hint'))model.state.round={...model.state.round!,hint:'Use под for under. It takes the instrumental case here.',hint_ru:'Предлог под здесь требует творительного падежа.'};
    if(url.endsWith('/answer')){
      if(model.failAnswer){model.failAnswer=false;return response({error:{code:'unavailable',message:'Please try saving again.'}},false);}
      model.state.phase='feedback';model.state.result={answer:body.answer,correct:false,expected_answer:['preposition:under','noun:instrumental'],feedback:'The place is right. Check the ending.',slot_results:[{id:'preposition',correct:true,expected:'preposition:under',text:'под',explanation:'Under is right.',explanation_ru:'Предлог выбран правильно.'},{id:'noun',correct:false,expected:'noun:instrumental',text:'столом',explanation:'Use столом for a position under the table.',explanation_ru:'Для положения под столом нужна форма столом.'}]};
    }
    if(url.endsWith('/continue')){model.state.round={...round,id:'next',scene_builder:{...round.scene_builder!,scene:'cat-on-table',scenario:'Barsik is on the table.'}};model.state.phase='play';model.state.round_index=1;model.state.result=null;}
    return response(model.state);
  });vi.stubGlobal('fetch',fetch);return {model,fetch,posts:()=>fetch.mock.calls.filter(([,request])=>request?.method==='POST')};
}
const click=async(name:string)=>fireEvent.click(await screen.findByRole('button',{name,exact:true}));
beforeEach(()=>{vi.stubGlobal('scrollTo',vi.fn());});afterEach(()=>vi.unstubAllGlobals());

describe('Describe the scene',()=>{
  it('starts with grammar topics and a game length without vocabulary restrictions',async()=>{
    const api=service();render(<JourneyGame gameId="scene-builder"/>);
    await screen.findByRole('button',{name:'Location'});
    expect(screen.queryByLabelText('Word source')).toBeNull();expect(screen.queryByText('Choose words')).toBeNull();
    await click('Verbs of motion');await click('10 rounds');await click('Let’s play');
    const request=JSON.parse(api.posts()[0][1]!.body as string);expect(request.options).toEqual({grammar_focus:'motion',rounds:10});
  });
  it('keeps the choice banks in place and requires every slot before checking',async()=>{
    const api=service();render(<JourneyGame sessionId="scene-test"/>);
    const check=await screen.findByRole('button',{name:'Check the sentence'});
    expect((check as HTMLButtonElement).disabled).toBe(true);
    await click('стол');expect((check as HTMLButtonElement).disabled).toBe(true);
    await click('под');expect((check as HTMLButtonElement).disabled).toBe(false);
    await click('на');expect(screen.getByRole('button',{name:'под'}).getAttribute('aria-pressed')).toBe('false');
    await click('под');expect(screen.getByRole('button',{name:'под'}).getAttribute('aria-pressed')).toBe('true');
    expect(screen.getAllByRole('button',{name:/^(на|под|за|стол|столе|столом)$/})).toHaveLength(6);
    expect(api.posts()).toHaveLength(0);
    await click('Check the sentence');await screen.findByText('Under is right.');
    expect(JSON.parse(api.posts()[0][1]!.body as string).answer).toEqual(['preposition:under','noun:nominative']);
    expect(screen.getByText('Use столом for a position under the table.')).toBeTruthy();
    expect(screen.getByText('Барсик сидит под столом.')).toBeTruthy();
    expect((screen.getByRole('button',{name:'столом'}).closest('fieldset') as HTMLFieldSetElement).disabled).toBe(true);
    await click('Next round');await screen.findByRole('button',{name:'Check the sentence'});
    expect((screen.getByRole('button',{name:'Check the sentence'}) as HTMLButtonElement).disabled).toBe(true);
  });
  it('preserves both selections through optional hints and retries the exact failed answer',async()=>{
    const api=service();render(<JourneyGame sessionId="scene-test"/>);
    await click('под');await click('стол');await click('Show a hint');await screen.findByText('Use под for under. It takes the instrumental case here.');
    expect(screen.getByRole('button',{name:'под'}).getAttribute('aria-pressed')).toBe('true');
    expect(screen.getByRole('button',{name:'стол'}).getAttribute('aria-pressed')).toBe('true');
    api.model.failAnswer=true;await click('Check the sentence');await screen.findByRole('alert');
    expect((screen.getByRole('button',{name:'на'}).closest('fieldset') as HTMLFieldSetElement).disabled).toBe(true);
    await click('Try again');await screen.findByText('Under is right.');
    const answers=api.posts().filter(([url])=>url.endsWith('/answer'));expect(answers).toHaveLength(2);expect(answers[1][1]?.body).toBe(answers[0][1]?.body);
  });
  it('uses the selected interface language for the situation, labels and hints',async()=>{
    service();render(<GameLanguage.Provider value="ru"><JourneyGame sessionId="scene-test"/></GameLanguage.Provider>);
    await screen.findByText('Барсик прячется внизу, под столом.');
    expect(screen.queryByText('Barsik is sitting under the table.')).toBeNull();
    expect(screen.getByRole('group',{name:'Выберите предлог'})).toBeTruthy();
    await click('Показать подсказку');await screen.findByText('Предлог под здесь требует творительного падежа.');
  });
  it('does not put the completed Russian answer or dictionary links on the unchecked scene',()=>{
    render(<SceneBuilder round={round} selected={[]} disabled={false} onChange={()=>{}}/>);
    expect(screen.queryByText('Барсик сидит под столом.')).toBeNull();
    expect(screen.queryByRole('link')).toBeNull();
    expect(screen.getByRole('img').getAttribute('aria-label')).toBe('Barsik is sitting under the table.');
  });
});

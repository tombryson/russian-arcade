import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/preact';
import { StepThroughConversation, type StepConversation } from './StepThroughConversation';

const scenario={title:'Tea for the journey',title_ru:'Чай в дорогу',description:'Order tea to take away.',description_ru:'Закажите чай с собой.',role:'Café worker',role_ru:'Сотрудник кафе',seed:'cafe-tea-v1'};
const firstTurn={id:'turn-one',ordinal:1,npc:{russian:'Здравствуйте! Что будете пить?',english:'Hello! What would you like to drink?'},intent:{en:'Ask for a tea, please.',ru:'Попросите чай.'},
  options:[{id:'tea',russian:'Чай, пожалуйста.'},{id:'yesterday',russian:'Вчера, пожалуйста.'},{id:'station',russian:'Вокзал, пожалуйста.'}],hint:null,answered:false,feedback:null,npc_audio_url:null,reply_audio_url:null};
const active:StepConversation={id:'step-one',state:'active',scenario,target_level:'A1',language:'en',created_at:1,error:null,retryable:false,turn_count:4,completed_turns:0,current_turn:firstTurn,transcript:[]};
const accepted:StepConversation={...active,completed_turns:1,current_turn:{...firstTurn,answered:true,feedback:{option_id:'tea',correct:true,explanation:{en:'A polite way to order.',ru:'Вежливый способ сделать заказ.'},english:'Tea, please.'}},
  transcript:[{id:'turn-one',ordinal:1,npc:firstTurn.npc,reply:{russian:'Чай, пожалуйста.',english:'Tea, please.'}}]};
const second:StepConversation={...active,completed_turns:1,current_turn:{...firstTurn,id:'turn-two',ordinal:2,npc:{russian:'С сахаром?',english:'With sugar?'},intent:{en:'Ask for no sugar.',ru:'Попросите без сахара.'},options:[{id:'no-sugar',russian:'Без сахара.'},{id:'with-sugar',russian:'С сахаром.'},{id:'tomorrow',russian:'Завтра.'}]},transcript:accepted.transcript};
const options={configured:true,audio_configured:true,scenario,sessions:[]};
const response=(value:unknown,ok=true)=>Promise.resolve({ok,json:async()=>value});
const failure=(message='Connection lost',code='request_failed')=>response({error:{message,code}},false);
function setup(handler:(url:string,init?:RequestInit)=>ReturnType<typeof response>=url=>response(url.includes('/options')?options:active)) {
  const fetch=vi.fn(handler);vi.stubGlobal('fetch',fetch);return fetch;
}
async function open() {await screen.findByRole('group',{name:'Ask for a tea, please.'});}
function choose(name='Чай, пожалуйста.') {fireEvent.click(screen.getByRole('radio',{name}));}
const body=(init?:RequestInit)=>JSON.parse(String(init?.body));
beforeEach(()=>{
  vi.spyOn(HTMLMediaElement.prototype,'pause').mockImplementation(()=>{});
  vi.spyOn(HTMLMediaElement.prototype,'play').mockResolvedValue(undefined);
});
afterEach(()=>{cleanup();vi.useRealTimers();vi.restoreAllMocks();vi.unstubAllGlobals();});

describe('Step-through conversation',()=>{
  it('opens the selected scenario without starting, recording, or generating audio',async()=>{
    const fetch=setup();const onBack=vi.fn();
    render(<StepThroughConversation scenarioId="cafe" targetLevel="A2" onBack={onBack}/>);
    expect(await screen.findByRole('heading',{name:'Tea for the journey'})).toBeTruthy();
    expect(screen.getByRole('button',{name:'Start step-through'})).toBeTruthy();
    expect(fetch.mock.calls).toHaveLength(1);
    expect(fetch.mock.calls[0][0]).toBe('/api/v1/step-conversations/options?scenario_id=cafe&level=A2');
    expect(fetch.mock.calls[0][1]?.method).toBe('GET');
    expect(screen.getByText(/recording is not needed/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'← Speaking'}));expect(onBack).toHaveBeenCalledOnce();
  });

  it('embeds only setup controls and starts the exact variant shown by the parent',async()=>{
    let finish!:(value:Awaited<ReturnType<typeof response>>)=>void;
    const fetch=setup(url=>url.includes('/options')?response({...options,sessions:[{id:'old',state:'completed',title:'Older conversation',target_level:'A1',created_at:1}]}):new Promise(resolve=>{finish=resolve;}) as ReturnType<typeof response>);
    const onPreparingChange=vi.fn();
    const {container}=render(<StepThroughConversation embeddedSetup scenarioId="cafe" scenarioSeed="live-selected-variant" targetLevel="A2" onPreparingChange={onPreparingChange}/>);
    fireEvent.click(await screen.findByRole('button',{name:'Start step-through'}));
    expect(screen.queryByRole('heading')).toBeNull();
    expect(screen.queryByRole('navigation')).toBeNull();
    expect(screen.queryByText('Order tea to take away.')).toBeNull();
    expect(screen.queryByText('Previous conversations')).toBeNull();
    expect(container.querySelector('.page')).toBeNull();
    expect(screen.getByText(/recording is not needed/)).toBeTruthy();
    expect(onPreparingChange.mock.calls.map(([value])=>value)).toEqual([false,true]);
    expect(body(fetch.mock.calls.find(([url])=>url==='/api/v1/step-conversations')?.[1])).toMatchObject({scenario_id:'cafe',scenario_seed:'live-selected-variant',target_level:'A2'});
    await act(async()=>{finish({ok:true,json:async()=>active});});
    await vi.waitFor(()=>expect(window.location.hash).toBe('#speaking/step/step-one'));
    expect(onPreparingChange).toHaveBeenLastCalledWith(false);
    expect(screen.getByRole('status').textContent).toBe('Opening your conversation…');
    expect(screen.queryByRole('group')).toBeNull();
  });

  it('keeps embedded setup locked through an uncertain start and its exact retry',async()=>{
    let failed=false;
    const fetch=setup(url=>{if(url.includes('/options'))return response(options);if(!failed){failed=true;return failure();}return response(active);});
    const onPreparingChange=vi.fn();
    render(<StepThroughConversation embeddedSetup scenarioId="cafe" scenarioSeed="live-selected-variant" onPreparingChange={onPreparingChange}/>);
    fireEvent.click(await screen.findByRole('button',{name:'Start step-through'}));
    const retry=await screen.findByRole('button',{name:'Try again'});
    expect(screen.getByRole('alert').textContent).toContain('Connection lost');
    expect(onPreparingChange.mock.calls.map(([value])=>value)).toEqual([false,true]);
    expect(screen.queryByRole('button',{name:'Reload scenario'})).toBeNull();
    fireEvent.click(retry);
    await vi.waitFor(()=>expect(onPreparingChange).toHaveBeenLastCalledWith(false));
    const creates=fetch.mock.calls.filter(([url])=>url==='/api/v1/step-conversations');
    expect(creates).toHaveLength(2);
    expect(body(creates[0][1])).toEqual(body(creates[1][1]));
  });

  it('releases the parent setup when unmounted during preparation and ignores the late response',async()=>{
    let finish!:(value:Awaited<ReturnType<typeof response>>)=>void;
    setup(url=>url.includes('/options')?response(options):new Promise(resolve=>{finish=resolve;}) as ReturnType<typeof response>);
    const onPreparingChange=vi.fn();
    const {unmount}=render(<StepThroughConversation embeddedSetup scenarioId="cafe" scenarioSeed="live-selected-variant" onPreparingChange={onPreparingChange}/>);
    fireEvent.click(await screen.findByRole('button',{name:'Start step-through'}));
    expect(onPreparingChange).toHaveBeenLastCalledWith(true);
    unmount();
    expect(onPreparingChange).toHaveBeenLastCalledWith(false);
    await act(async()=>{finish({ok:true,json:async()=>active});});
    expect(window.location.hash).toBe('');
  });

  it('does not silently choose a different variant when embedded without the parent seed',async()=>{
    const fetch=setup();
    render(<StepThroughConversation embeddedSetup scenarioId="cafe"/>);
    expect(await screen.findByText('No conversation is available for this level yet.')).toBeTruthy();
    expect(screen.queryByRole('button',{name:'Start step-through'})).toBeNull();
    expect(fetch.mock.calls.every(([,init])=>init?.method==='GET')).toBe(true);
  });

  it('starts explicitly with the chosen variant and suppresses repeated clicks',async()=>{
    let finish!:(value:Awaited<ReturnType<typeof response>>)=>void;
    const fetch=setup((url)=>url.includes('/options')?response(options):new Promise(resolve=>{finish=resolve;}) as ReturnType<typeof response>);
    render(<StepThroughConversation scenarioId="cafe" scenarioSeed="chosen-variant" targetLevel="A2"/>);
    const start=await screen.findByRole('button',{name:'Start step-through'});
    fireEvent.click(start);fireEvent.click(start);
    const creates=fetch.mock.calls.filter(([url])=>url==='/api/v1/step-conversations');
    expect(creates).toHaveLength(1);
    expect(body(creates[0][1])).toMatchObject({scenario_id:'cafe',scenario_seed:'chosen-variant',target_level:'A2',language:'en',submission_id:expect.any(String)});
    expect(screen.getByRole('button',{name:'Preparing your conversation…'}).hasAttribute('disabled')).toBe(true);
    await act(async()=>{finish({ok:true,json:async()=>active});});
    await vi.waitFor(()=>expect(window.location.hash).toBe('#speaking/step/step-one'));
    await open();
  });

  it('requires Check reply and supports correcting a rejected reply without advancing',async()=>{
    const wrong={...active,current_turn:{...firstTurn,feedback:{option_id:'station',correct:false,explanation:{en:'Name a drink here.',ru:'Здесь нужно назвать напиток.'},english:'Station, please.'}}};
    const fetch=setup((url,init)=>url.endsWith('/answer')?response(body(init).option_id==='station'?wrong:accepted):response(active));
    render(<StepThroughConversation sessionId="step-one"/>);await open();
    expect(screen.getByRole('button',{name:'Check reply'}).hasAttribute('disabled')).toBe(true);
    choose('Вокзал, пожалуйста.');
    expect(fetch.mock.calls).toHaveLength(1);
    fireEvent.submit(screen.getByRole('group').closest('form')!);
    expect(await screen.findByText('Try another reply.')).toBeTruthy();
    expect(screen.getByText('Name a drink here.')).toBeTruthy();
    expect(screen.queryByText('Station, please.')).toBeNull();
    expect(screen.queryByRole('button',{name:'Continue'})).toBeNull();
    choose();fireEvent.click(screen.getByRole('button',{name:'Check reply'}));
    expect(await screen.findByText('Tea, please.')).toBeTruthy();
    expect(screen.getByRole('button',{name:'Continue'})).toBeTruthy();
    expect(fetch.mock.calls.filter(([url])=>url.endsWith('/answer'))).toHaveLength(2);
    expect(fetch.mock.calls.some(([url])=>url.endsWith('/next'))).toBe(false);
    expect(document.activeElement).toBe(screen.getByText('Your reply').closest('[role="status"]'));
  });

  it('requests a hint only on demand and keeps the chosen answer',async()=>{
    const fetch=setup(url=>response(url.endsWith('/hint')?{...active,current_turn:{...firstTurn,hint:{en:'Use the name of the drink.',ru:'Назовите напиток.'}}}:active));
    render(<StepThroughConversation sessionId="step-one"/>);await open();choose();
    expect(screen.queryByText('Use the name of the drink.')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Show a hint'}));
    expect(await screen.findByText('Use the name of the drink.')).toBeTruthy();
    expect((screen.getByRole('radio',{name:'Чай, пожалуйста.'}) as HTMLInputElement).checked).toBe(true);
    expect(body(fetch.mock.calls.find(([url])=>url.endsWith('/hint'))?.[1])).toEqual({turn_id:'turn-one'});
  });

  it('resumes an accepted reply without submitting it again, then continues explicitly',async()=>{
    const fetch=setup(url=>response(url.endsWith('/next')?second:accepted));
    render(<StepThroughConversation sessionId="step-one"/>);
    await screen.findByRole('button',{name:'Continue'});
    expect(screen.queryByRole('radio')).toBeNull();
    expect(screen.queryByText('Conversation so far')).toBeNull();
    expect(fetch.mock.calls.every(([,init])=>init?.method==='GET')).toBe(true);
    fireEvent.click(screen.getByRole('button',{name:'Continue'}));
    expect(await screen.findByRole('group',{name:'Ask for no sugar.'})).toBeTruthy();
    expect(screen.getByText('Step 2 of 4')).toBeTruthy();
    expect(screen.getByText('Conversation so far').closest('details')?.open).toBe(false);
    expect(document.activeElement?.textContent).toBe('С сахаром?');
    expect(body(fetch.mock.calls.find(([url])=>url.endsWith('/next'))?.[1])).toEqual({turn_id:'turn-one'});
  });

  it('prepares reply audio only when requested and reuses the saved recording',async()=>{
    const fetch=setup(url=>response(url.endsWith('/audio')?{...accepted,current_turn:{...accepted.current_turn!,reply_audio_url:'/private/reply.mp3'}}:accepted));
    const {container}=render(<StepThroughConversation sessionId="step-one"/>);
    fireEvent.click(await screen.findByRole('button',{name:'Listen to your reply'}));
    const pause=await screen.findByRole('button',{name:'Pause your reply'});
    const recording=container.querySelector('audio')!;
    expect(recording.getAttribute('src')).toBe('/private/reply.mp3');
    expect(recording.hidden).toBe(true);
    expect(recording.hasAttribute('controls')).toBe(false);
    await vi.waitFor(()=>expect(HTMLMediaElement.prototype.play).toHaveBeenCalledOnce());
    vi.mocked(HTMLMediaElement.prototype.pause).mockClear();
    fireEvent.click(pause);
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole('button',{name:'Listen to your reply'}));
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalledTimes(2);
    fireEvent.ended(recording);
    expect(screen.getByRole('button',{name:'Listen to your reply'})).toBeTruthy();
    expect(fetch.mock.calls.filter(([url])=>url.endsWith('/audio'))).toHaveLength(1);
    expect(body(fetch.mock.calls.find(([url])=>url.endsWith('/audio'))?.[1])).toEqual({kind:'reply',turn_id:'turn-one'});
  });

  it('pauses the previous speaker when listening to the reply and resets on the next turn',async()=>{
    const withAudio={...accepted,current_turn:{...accepted.current_turn!,npc_audio_url:'/private/npc.mp3',reply_audio_url:'/private/reply.mp3'}};
    setup(url=>response(url.endsWith('/next')?{...second,current_turn:{...second.current_turn!,npc_audio_url:'/private/next.mp3'}}:withAudio));
    const {container}=render(<StepThroughConversation sessionId="step-one"/>);
    fireEvent.click(await screen.findByRole('button',{name:'Listen to the other speaker'}));
    expect(screen.getByRole('button',{name:'Pause the other speaker'})).toBeTruthy();
    vi.mocked(HTMLMediaElement.prototype.pause).mockClear();
    fireEvent.click(screen.getByRole('button',{name:'Listen to your reply'}));
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalledOnce();
    expect(vi.mocked(HTMLMediaElement.prototype.pause).mock.instances[0]).toBe(container.querySelector('audio[src="/private/npc.mp3"]'));
    expect(screen.getByRole('button',{name:'Listen to the other speaker'})).toBeTruthy();
    expect(screen.getByRole('button',{name:'Pause your reply'})).toBeTruthy();
    vi.mocked(HTMLMediaElement.prototype.pause).mockClear();
    fireEvent.click(screen.getByRole('button',{name:'Continue'}));
    await screen.findByRole('group',{name:'Ask for no sugar.'});
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalledTimes(2);
    expect(screen.getByRole('button',{name:'Listen to the other speaker'})).toBeTruthy();
    expect(screen.queryByRole('button',{name:/Pause/})).toBeNull();
    expect(container.querySelectorAll('audio')).toHaveLength(1);
    expect(container.querySelector('audio')?.getAttribute('src')).toBe('/private/next.mp3');
  });

  it('retries an uncertain answer with the same submission ID and payload',async()=>{
    let failed=false;
    const fetch=setup((url)=>{if(url.endsWith('/answer')){if(!failed){failed=true;return failure();}return response(accepted);}return response(active);});
    render(<StepThroughConversation sessionId="step-one"/>);await open();choose();
    fireEvent.click(screen.getByRole('button',{name:'Check reply'}));
    fireEvent.click(await screen.findByRole('button',{name:'Try again'}));
    await screen.findByRole('button',{name:'Continue'});
    const calls=fetch.mock.calls.filter(([url])=>url.endsWith('/answer'));
    expect(calls).toHaveLength(2);expect(body(calls[0][1])).toEqual(body(calls[1][1]));
  });

  it('retries an uncertain start with the original variant and submission ID',async()=>{
    let failed=false;
    const fetch=setup(url=>{if(url.includes('/options'))return response(options);if(!failed){failed=true;return failure();}return response(active);});
    render(<StepThroughConversation scenarioId="cafe"/>);
    fireEvent.click(await screen.findByRole('button',{name:'Start step-through'}));
    const retry=await screen.findByRole('button',{name:'Try again'});
    expect(screen.queryByRole('button',{name:'Reload scenario'})).toBeNull();
    fireEvent.click(retry);await open();
    const creates=fetch.mock.calls.filter(([url])=>url==='/api/v1/step-conversations');
    expect(creates).toHaveLength(2);expect(body(creates[0][1])).toEqual(body(creates[1][1]));
  });

  it('requires a read-only reload after a stale turn and never replays the old answer',async()=>{
    let reads=0;
    const fetch=setup(url=>url.endsWith('/answer')?failure('This turn has changed.','stale_turn'):response(++reads===1?active:second));
    render(<StepThroughConversation sessionId="step-one"/>);await open();choose();
    fireEvent.click(screen.getByRole('button',{name:'Check reply'}));
    await screen.findByText('This turn has changed.');
    expect(screen.queryByRole('button',{name:'Try again'})).toBeNull();
    expect(screen.getByRole('button',{name:'Check reply'}).hasAttribute('disabled')).toBe(true);
    fireEvent.click(screen.getByRole('button',{name:'Reload conversation'}));
    await screen.findByRole('group',{name:'Ask for no sugar.'});
    expect(fetch.mock.calls.filter(([,init])=>init?.method==='POST')).toHaveLength(1);
    expect(screen.queryByText('This turn has changed.')).toBeNull();
  });

  it('blocks further activity when the account changed',async()=>{
    setup(url=>url.endsWith('/answer')?failure('Your account changed.','account_changed'):response(active));
    render(<StepThroughConversation sessionId="step-one"/>);await open();choose();
    fireEvent.click(screen.getByRole('button',{name:'Check reply'}));
    expect(await screen.findByRole('button',{name:'Reload page'})).toBeTruthy();
    expect(screen.queryByRole('button',{name:'Try again'})).toBeNull();
    expect(screen.getByRole('button',{name:'Check reply'}).hasAttribute('disabled')).toBe(true);
  });

  it('offers an explicit retry for persisted preparation failure',async()=>{
    const fetch=setup(url=>response(url.endsWith('/retry')?active:{...active,state:'failed',current_turn:null,error:'Preparation is unavailable.',retryable:true}));
    render(<StepThroughConversation sessionId="step-one"/>);
    expect(await screen.findByText('Preparation is unavailable.')).toBeTruthy();
    expect(fetch.mock.calls.every(([,init])=>init?.method==='GET')).toBe(true);
    fireEvent.click(screen.getByRole('button',{name:'Try preparing again'}));await open();
    expect(body(fetch.mock.calls.find(([url])=>url.endsWith('/retry'))?.[1])).toEqual({});
  });

  it('offers manual recovery when preparation expired instead of polling forever',async()=>{
    const fetch=setup(url=>response(url.endsWith('/retry')?active:{...active,state:'preparing',current_turn:null,error:null,retryable:true}));
    render(<StepThroughConversation sessionId="step-one"/>);
    fireEvent.click(await screen.findByRole('button',{name:'Try preparing again'}));await open();
    expect(fetch.mock.calls.map(([url])=>url)).toEqual(['/api/v1/step-conversations/step-one','/api/v1/step-conversations/step-one/retry']);
  });

  it('polls preparation using only reads until the saved conversation is ready',async()=>{
    let reads=0;
    const fetch=setup(()=>response(++reads===1?{...active,state:'preparing',current_turn:null}:active));
    render(<StepThroughConversation sessionId="step-one"/>);
    expect(await screen.findByText('Preparing your conversation…')).toBeTruthy();
    await screen.findByRole('group',{name:'Ask for a tea, please.'},{timeout:3000});
    expect(fetch.mock.calls).toHaveLength(2);
    expect(fetch.mock.calls.every(([,init])=>init?.method==='GET')).toBe(true);
  });

  it('keeps reading and answering available when audio generation is not configured',async()=>{
    setup(()=>response({...active,audio_configured:false}));
    render(<StepThroughConversation sessionId="step-one"/>);await open();
    expect(screen.queryByRole('button',{name:'Listen to the other speaker'})).toBeNull();
    choose();expect(screen.getByRole('button',{name:'Check reply'}).hasAttribute('disabled')).toBe(false);
  });

  it('keeps unavailable scenario variants from offering a broken Start action',async()=>{
    const fetch=setup(()=>response({...options,scenario:null}));
    render(<StepThroughConversation scenarioId="cafe" targetLevel="B2"/>);
    expect(await screen.findByText('No conversation is available for this level yet.')).toBeTruthy();
    expect(screen.queryByRole('button',{name:'Start step-through'})).toBeNull();
    expect(fetch.mock.calls.every(([,init])=>init?.method==='GET')).toBe(true);
  });

  it('keeps blocked audio playback recoverable with the Listen button',async()=>{
    vi.mocked(HTMLMediaElement.prototype.play).mockRejectedValueOnce(new DOMException('Permission needed','NotAllowedError'));
    setup(()=>response({...accepted,current_turn:{...accepted.current_turn!,reply_audio_url:'/private/reply.mp3'}}));
    render(<StepThroughConversation sessionId="step-one"/>);
    fireEvent.click(await screen.findByRole('button',{name:'Listen to your reply'}));
    expect(await screen.findByText('Audio is ready. Select Listen to play it.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Listen to your reply'}));
    expect(screen.getByRole('button',{name:'Pause your reply'})).toBeTruthy();
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalledTimes(2);
    expect(screen.queryByText('Audio is ready. Select Listen to play it.')).toBeNull();
    expect(screen.getByRole('button',{name:'Continue'}).hasAttribute('disabled')).toBe(false);
  });

  it('does not report an interrupted playback request after the learner pauses it',async()=>{
    let reject!:(reason:unknown)=>void;
    vi.mocked(HTMLMediaElement.prototype.play).mockImplementationOnce(()=>new Promise<void>((_,fail)=>{reject=fail;}));
    setup(()=>response({...active,current_turn:{...firstTurn,npc_audio_url:'/private/npc.mp3'}}));
    render(<StepThroughConversation sessionId="step-one"/>);await open();
    fireEvent.click(screen.getByRole('button',{name:'Listen to the other speaker'}));
    fireEvent.click(screen.getByRole('button',{name:'Pause the other speaker'}));
    await act(async()=>reject(new DOMException('Playback interrupted','AbortError')));
    expect(screen.getByRole('button',{name:'Listen to the other speaker'})).toBeTruthy();
    expect(screen.queryByText('Audio could not play. Try again.')).toBeNull();
  });

  it('lets the learner continue choosing replies after optional audio preparation fails',async()=>{
    setup(url=>url.endsWith('/audio')?failure('Audio is unavailable.'):response(active));
    render(<StepThroughConversation sessionId="step-one"/>);await open();
    fireEvent.click(screen.getByRole('button',{name:'Listen to the other speaker'}));
    await screen.findByText('Audio is unavailable.');choose();
    expect(screen.getByRole('button',{name:'Check reply'}).hasAttribute('disabled')).toBe(false);
  });

  it('shows the server reward and refreshes progression once when the last reply is completed',async()=>{
    const completed={...accepted,state:'completed',current_turn:null,completed_turns:4,reward:{amount:3,basis:'guided_step_completion'},ending:{russian:'До свидания!',english:'Goodbye!'}};
    setup(url=>response(url.endsWith('/next')?completed:accepted));
    const progression=vi.fn();window.addEventListener('lingo:progression',progression);
    try {
      const {unmount}=render(<StepThroughConversation sessionId="step-one"/>);
      fireEvent.click(await screen.findByRole('button',{name:'Continue'}));
      expect(await screen.findByText('Lingocoins earned: 3')).toBeTruthy();
      expect(progression).toHaveBeenCalledOnce();
      unmount();setup(()=>response(completed));
      render(<StepThroughConversation sessionId="step-one"/>);
      await screen.findByRole('heading',{name:'Conversation complete'});
      expect(progression).toHaveBeenCalledOnce();
    } finally {window.removeEventListener('lingo:progression',progression);}
  });

  it('keeps the ending and saved conversation available without claiming fluency',async()=>{
    const fetch=setup(()=>response({...accepted,state:'completed',completed_turns:4,current_turn:null,ending:{russian:'Спасибо! Хорошего дня!',english:'Thank you! Have a good day!'}}));
    render(<StepThroughConversation sessionId="step-one"/>);
    expect(await screen.findByRole('heading',{name:'Conversation complete'})).toBeTruthy();
    expect(screen.getByText('Спасибо! Хорошего дня!')).toBeTruthy();
    expect(screen.getByText('Review conversation').closest('details')?.open).toBe(false);
    expect(screen.getByRole('link',{name:'Choose another conversation'}).getAttribute('href')).toBe('#speaking/step');
    expect(screen.queryByText(/fluency|pronunciation score/i)).toBeNull();
    expect(fetch.mock.calls.every(([,init])=>init?.method==='GET')).toBe(true);
  });

  it('uses Russian intent and controls while keeping the three replies in Russian',async()=>{
    setup(()=>response(active));render(<StepThroughConversation sessionId="step-one" language="ru"/>);
    const group=await screen.findByRole('group',{name:'Попросите чай.'});
    expect(within(group).getAllByRole('radio')).toHaveLength(3);
    expect(screen.getByRole('button',{name:'Проверить ответ'})).toBeTruthy();
    expect(screen.getByRole('button',{name:'Показать подсказку'})).toBeTruthy();
    expect(screen.getByRole('heading',{name:'Чай в дорогу'})).toBeTruthy();
  });

  it('ignores a late start response after leaving the screen',async()=>{
    let finish!:(value:Awaited<ReturnType<typeof response>>)=>void;
    setup(url=>url.includes('/options')?response(options):new Promise(resolve=>{finish=resolve;}) as ReturnType<typeof response>);
    const {unmount}=render(<StepThroughConversation scenarioId="cafe"/>);
    fireEvent.click(await screen.findByRole('button',{name:'Start step-through'}));unmount();
    await act(async()=>{finish({ok:true,json:async()=>active});});
    expect(window.location.hash).toBe('');
  });

  it('resets to a new scenario preview when the parent changes selection',async()=>{
    const fetch=setup(url=>response(url.includes('/options')?options:active));
    const {rerender}=render(<StepThroughConversation sessionId="step-one"/>);await open();
    rerender(<StepThroughConversation scenarioId="shop" targetLevel="A2"/>);
    expect(await screen.findByRole('button',{name:'Start step-through'})).toBeTruthy();
    expect(fetch.mock.calls.at(-1)?.[0]).toBe('/api/v1/step-conversations/options?scenario_id=shop&level=A2');
    expect(screen.queryByRole('radio')).toBeNull();
  });
});

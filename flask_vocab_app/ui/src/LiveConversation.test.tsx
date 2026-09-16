import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/preact';
import { LiveConversation } from './LiveConversation';
import { LiveConnection, captionRows, type Caption } from './live-connection';

const options={configured:true,notes_configured:true,max_seconds:300,sessions:[]};
const catalogue={activity:{id:'speaking',title:'Speaking',title_ru:'Разговорная практика'},scenarios:[
  {id:'cafe',title:'At the café',title_ru:'В кафе',description:'Order something to eat and drink.',description_ru:'Закажите еду и напитки.',role:'Café worker',role_ru:'Сотрудник кафе',icon:'☕',sign:'КАФЕ',variant_count:8},
  {id:'shop',title:'At the shop',title_ru:'В магазине',description:'Find what you need and ask the price.',description_ru:'Найдите нужные покупки и узнайте цену.',role:'Shop assistant',role_ru:'Продавец',icon:'🛍️',sign:'МАГАЗИН',variant_count:3},
  {id:'directions',title:'Find your way',title_ru:'Как пройти',description:'Ask someone for directions.',description_ru:'Спросите дорогу.',role:'Passer-by',role_ru:'Прохожий',icon:'🧭',sign:'ГОРОД',variant_count:3},
  {id:'station',title:'At the station',title_ru:'На вокзале',description:'Plan a train journey.',description_ru:'Спланируйте поездку.',role:'Ticket clerk',role_ru:'Кассир',icon:'🚆',sign:'ВОКЗАЛ',variant_count:3},
  {id:'meet-someone',title:'Meet someone new',title_ru:'Знакомство',description:'Introduce yourself and get to know someone.',description_ru:'Познакомьтесь с собеседником.',role:'New acquaintance',role_ru:'Новый знакомый',icon:'👋',sign:'ПРИВЕТ',variant_count:3},
].map(item=>({...item,levels:['A1','A2'],available:true}))};
const saved={id:'live-one',state:'new',connected:false,finalized:false,created_at:1,captions:[],recordings:[]};
const scenario={seed:'cafe-warm-drink-v1',title:'Time to warm up',title_ru:'Пора согреться',description:'Choose a hot drink, ask for it without sugar, and find out the price.',description_ru:'Выберите горячий напиток, попросите его без сахара и узнайте цену.',opening:'Здравствуйте! Хотите что-нибудь горячее?',
  goals:['Choose a hot drink','Ask for no sugar','Ask the price'],goals_ru:['Выберите горячий напиток','Попросите без сахара','Спросите цену'],goal_ids:['hot_drink','no_sugar','price'],menu:{чай:90,кофе:140,какао:160}};
const shopScenario={seed:'shop-notebook-v1',scenario_id:'shop',category_title:'At the shop',category_title_ru:'В магазине',role:'Shop assistant',role_ru:'Продавец',icon:'🛍️',sign:'МАГАЗИН',
  title:'A notebook for class',title_ru:'Тетрадь для занятий',description:'Find a notebook and ask the price.',description_ru:'Найдите тетрадь и узнайте цену.',opening:'Здравствуйте! Что вы ищете?',
  goals:['Find a notebook','Ask the price'],goals_ru:['Найдите тетрадь','Спросите цену'],goal_ids:['notebook','price'],menu:{},
  reference:{title:'Shopping list',title_ru:'Список покупок',items:[{label:'Notebook',label_ru:'Тетрадь',value:'One, lined',value_ru:'Одна, в линейку'}]}};
const recording={id:'r',ordinal:1,state:'ready',audio_url:'/private/r.wav',sample_count:24000,sample_rate:24000,retryable:false,transcript:{text:'Я хочу чай без сахар.'},assessment:null};
const report={basis:'audio_review',rubric_version:'speaking-v1',model:'test',transcript:'Я хочу чай без сахар.',speech_status:'russian',
  grammar:{score:3,reason:'Your order was clear. One ending needs a small change.',evidence:['без сахар']},fluency:{score:4,reason:'Your request flowed with a short pause.',evidence:['Я хочу чай']},
  goals:[{id:'hot_drink',status:'completed',evidence:['чай']},{id:'no_sugar',status:'completed',evidence:['без сахар']},{id:'price',status:'not_yet',evidence:[]}],
  summary:'You made your order understood and kept the conversation going.',next_step:'Try saying без сахара as one short phrase.',
  corrections:[{original:'без сахар',replacement:'без сахара',explanation:'Use the genitive after без.',category:'Case'}],uncertainty:''};
const response=(value:unknown)=>Promise.resolve({ok:true,json:async()=>value});
function setup(value:unknown=saved) {
  const fetch=vi.fn((url:string)=>response(url.includes('/scenarios')?catalogue:url.includes('/options')?{...options,scenario}:url.endsWith('/connect')?{sdp:'v=0 answer'}:value));
  vi.stubGlobal('fetch',fetch);return fetch;
}
async function chooseCafe() {
  fireEvent.click(await scenarioButton('At the café'));
  await screen.findByRole('heading',{name:'Time to warm up'});
}
async function scenarioButton(name:string,level='A1') {
  return within(await screen.findByRole('region',{name:level})).findByRole('button',{name});
}
function fakeMedia() {
  const track={enabled:true,stop:vi.fn()};
  const microphone={getTracks:()=>[track],getAudioTracks:()=>[track]};
  const getUserMedia=vi.fn().mockResolvedValue(microphone);
  vi.stubGlobal('navigator',{mediaDevices:{getUserMedia}});
  const speaker={autoplay:false,srcObject:null,play:vi.fn().mockResolvedValue(undefined),pause:vi.fn()};
  vi.stubGlobal('Audio',class { constructor(){return speaker;} });
  const events={readyState:'open',onmessage:(_m:{data:string})=>{},onclose:()=>{},send:vi.fn(),close:vi.fn()};
  class Peer extends EventTarget {
    localDescription={sdp:'v=0\r\nm=audio test'};iceGatheringState='complete';connectionState='connected';
    ontrack=()=>{};onconnectionstatechange=()=>{};
    addTrack=vi.fn();createDataChannel=()=>events;createOffer=vi.fn().mockResolvedValue({type:'offer',sdp:'v=0'});
    setLocalDescription=vi.fn().mockResolvedValue(undefined);setRemoteDescription=vi.fn().mockResolvedValue(undefined);close=vi.fn();
  }
  vi.stubGlobal('RTCPeerConnection',Peer);
  return {getUserMedia,track,microphone,events,speaker};
}
beforeEach(()=>{vi.stubGlobal('scrollTo',vi.fn());});
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals();});

describe('Speaking activity',()=>{
  it('opens a suggested directions scenario without starting the microphone',async()=>{
    const fetch=setup();const {getUserMedia}=fakeMedia();
    render(<LiveConversation initialScenarioId="directions" />);
    await vi.waitFor(()=>expect(fetch.mock.calls.some(([url])=>url==='/api/v1/live-conversations/options?scenario_id=directions&level=A1')).toBe(true));
    expect(getUserMedia).not.toHaveBeenCalled();
    expect(fetch.mock.calls.some(([url])=>url==='/api/v1/live-conversations')).toBe(false);
  });
  it('omits English from saved captions and recording transcripts',async()=>{
    setup({...saved,state:'completed',captions:[
      {type:'session.input_transcript.delta',delta:"I'd like some coffee and some tea",start_ms:0,end_ms:1000},
      {type:'session.output_transcript.delta',delta:'Извините, я не понимаю.',start_ms:1500,end_ms:2300},
    ],recordings:[{id:'r',ordinal:1,state:'ready',audio_url:'/private/r.wav',sample_count:24000,sample_rate:24000,retryable:false,
      transcript:{text:"I'm going on holiday on Thursday."},assessment:null}]});
    fakeMedia();render(<LiveConversation sessionId="live-one" />);
    await screen.findByText('Извините, я не понимаю.');
    expect(screen.queryByText(/I'd like some coffee|I'm going on holiday/)).toBeNull();
    expect(screen.getByText('No Russian transcript to show.')).toBeTruthy();
    expect(screen.getByLabelText('Your recording 1').getAttribute('src')).toBe('/private/r.wav');
  });
  it('opens the scenario catalogue and leaves the microphone off until Start',async()=>{
    const fetch=setup();const {getUserMedia}=fakeMedia();render(<LiveConversation />);
    await screen.findByRole('region',{name:'Choose a scenario'});
    expect(await scenarioButton('At the café')).toBeTruthy();
    expect(within(screen.getByRole('region',{name:'A1'})).getByRole('button',{name:'At the shop'})).toBeTruthy();
    expect(within(screen.getByRole('region',{name:'A1'})).getByRole('button',{name:'Find your way'})).toBeTruthy();
    expect(within(screen.getByRole('region',{name:'A1'})).getByRole('button',{name:'At the station'})).toBeTruthy();
    expect(within(screen.getByRole('region',{name:'A1'})).getByRole('button',{name:'Meet someone new'})).toBeTruthy();
    expect(screen.queryByRole('button',{name:/Start talking/})).toBeNull();
    expect(screen.getByRole('heading',{name:'Speaking'})).toBeTruthy();
    expect(screen.queryByRole('heading',{name:'Live conversation'})).toBeNull();
    expect(screen.getByText('Previous conversations')).toBeTruthy();
    expect(screen.getByText('Developer tools').closest('details')?.open).toBe(false);
    expect(screen.getByText(/Speech lab/).getAttribute('href')).toBe('#speaking/lab');
    expect(getUserMedia).not.toHaveBeenCalled();expect(screen.queryByText(/\d+ ₽/)).toBeNull();
    expect(screen.queryByRole('heading',{name:'Time to warm up'})).toBeNull();
    expect(screen.queryByText(/PIN|grown-up/i)).toBeNull();
    expect(fetch.mock.calls.map(([url])=>url)).toEqual(['/api/v1/live-conversations/scenarios']);
  });
  it('loads a shop task and starts the selected scenario with its own reference, role and greeting',async()=>{
    const value={...saved,scenario_id:'shop',scenario:shopScenario};
    const fetch=vi.fn((url:string,_init?:RequestInit)=>response(url.includes('/scenarios') ? catalogue : url.includes('/options') ? {...options,scenario:shopScenario} : url.endsWith('/connect') ? {sdp:'v=0 answer'} : value));
    vi.stubGlobal('fetch',fetch);const {getUserMedia,events}=fakeMedia();render(<LiveConversation />);
    fireEvent.click(await scenarioButton('At the shop'));
    await screen.findByRole('heading',{name:'A notebook for class'});
    expect(fetch.mock.calls.some(([url])=>url==='/api/v1/live-conversations/options?scenario_id=shop&level=A1')).toBe(true);
    expect(screen.getByLabelText('Shopping list').textContent).toContain('Notebook');
    expect(screen.getByText('One, lined')).toBeTruthy();
    expect(screen.queryByLabelText('Café menu')).toBeNull();expect(screen.queryByText('КАФЕ')).toBeNull();
    expect(getUserMedia).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button',{name:/Start talking/}));
    await vi.waitFor(()=>expect(fetch.mock.calls.some(([url])=>url.endsWith('/connect'))).toBe(true));
    const request=fetch.mock.calls.find(([url])=>url==='/api/v1/live-conversations')!;
    expect(JSON.parse(request[1]?.body as string)).toMatchObject({scenario_id:'shop',scenario_seed:shopScenario.seed,target_level:'A1'});
    events.onmessage({data:JSON.stringify({type:'session.started',event_id:'start'})});
    expect(JSON.parse(events.send.mock.calls[0][0]).content).toContain(shopScenario.opening);
    events.onmessage({data:JSON.stringify({type:'session.output_transcript.delta',event_id:'hello',delta:'Здравствуйте! Что вы ищете?',start_ms:0,end_ms:1000})});
    expect(await screen.findByText('Shop assistant')).toBeTruthy();
    expect(screen.queryByText('Café worker')).toBeNull();
  });
  it('lets the learner return to the catalogue and choose another place without opening a call',async()=>{
    const fetch=vi.fn((url:string)=>response(url.includes('/scenarios') ? catalogue : {...options,scenario:url.includes('scenario_id=shop') ? shopScenario : scenario}));
    vi.stubGlobal('fetch',fetch);const {getUserMedia}=fakeMedia();render(<LiveConversation />);
    await chooseCafe();fireEvent.click(screen.getByRole('button',{name:'← All scenarios'}));
    fireEvent.click(await scenarioButton('At the shop'));
    await screen.findByRole('heading',{name:'A notebook for class'});
    expect(screen.queryByRole('heading',{name:'Time to warm up'})).toBeNull();
    expect(getUserMedia).not.toHaveBeenCalled();expect(fetch.mock.calls.some(([url])=>url==='/api/v1/live-conversations')).toBe(false);
  });
  it('ignores an old preview response after switching to a different scenario',async()=>{
    let resolveCafe:(value:unknown)=>void=()=>{};
    const fetch=vi.fn((url:string)=>url.includes('scenario_id=cafe') ? new Promise(resolve=>{resolveCafe=resolve;}) : response(url.includes('/scenarios') ? catalogue : {...options,scenario:shopScenario}));
    vi.stubGlobal('fetch',fetch);render(<LiveConversation />);
    fireEvent.click(await scenarioButton('At the café'));
    fireEvent.click(await screen.findByRole('button',{name:'← All scenarios'}));
    fireEvent.click(await scenarioButton('At the shop'));
    await screen.findByRole('heading',{name:'A notebook for class'});
    resolveCafe(await response({...options,scenario}));
    await new Promise(resolve=>setTimeout(resolve,0));
    expect(screen.getByRole('heading',{name:'A notebook for class'})).toBeTruthy();
    expect(screen.queryByRole('heading',{name:'Time to warm up'})).toBeNull();
  });
  it('offers a read-only retry when the scenario catalogue cannot load',async()=>{
    let available=false;
    const fetch=vi.fn((url:string)=>url.endsWith('/progression') ? response({preferred_level:'A1'}) : available ? response(catalogue) : Promise.reject(new Error('The scenarios could not load.')));
    vi.stubGlobal('fetch',fetch);const {getUserMedia}=fakeMedia();render(<LiveConversation />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent','The scenarios could not load.');
    available=true;fireEvent.click(screen.getByRole('button',{name:'Try loading scenarios again'}));
    expect(await scenarioButton('At the station')).toBeTruthy();
    expect(getUserMedia).not.toHaveBeenCalled();expect(fetch).toHaveBeenCalledTimes(2);
  });
  it('shows Russian catalogue labels and the chosen reference in Russian',async()=>{
    vi.stubGlobal('fetch',vi.fn((url:string)=>response(url.includes('/scenarios') ? catalogue : {...options,scenario:shopScenario})));
    render(<LiveConversation language="ru" />);
    fireEvent.click(await scenarioButton('В магазине'));
    await screen.findByRole('heading',{name:'Тетрадь для занятий'});
    expect(screen.getByLabelText('Список покупок').textContent).toContain('Одна, в линейку');
    expect(screen.queryByText('Notebook')).toBeNull();
  });
  it('shows A1 activities followed by A2 activities without a level selector',async()=>{
    const fetch=setup();const {getUserMedia}=fakeMedia();render(<LiveConversation />);
    await scenarioButton('At the café');
    const a1=screen.getByRole('region',{name:'A1'});const a2=screen.getByRole('region',{name:'A2'});
    expect(screen.getAllByRole('heading').filter(heading=>['A1','A2'].includes(heading.textContent || '')).map(heading=>heading.textContent)).toEqual(['A1','A2']);
    expect(a1.compareDocumentPosition(a2) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(a1).getAllByRole('button')).toHaveLength(5);
    expect(within(a2).getAllByRole('button')).toHaveLength(5);
    expect(a2.classList.contains('speaking-level-group-muted')).toBe(true);
    expect(screen.queryByRole('tablist')).toBeNull();
    expect(screen.queryByRole('tab')).toBeNull();
    expect(screen.queryByRole('combobox')).toBeNull();
    expect(screen.queryByRole('heading',{name:'B1'})).toBeNull();
    expect(screen.queryByRole('heading',{name:'B2'})).toBeNull();
    expect(fetch.mock.calls.map(([url])=>url)).toEqual(['/api/v1/live-conversations/scenarios']);
    expect(getUserMedia).not.toHaveBeenCalled();
  });
  it('lists each scenario only under levels with authored content',async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>response({...catalogue,scenarios:[
      {...catalogue.scenarios[0],levels:['A1']},
      {...catalogue.scenarios[1],levels:['A2']},
    ]})));
    render(<LiveConversation />);
    expect(await scenarioButton('At the café')).toBeTruthy();
    expect(await scenarioButton('At the shop','A2')).toBeTruthy();
    expect(within(screen.getByRole('region',{name:'A1'})).queryByRole('button',{name:'At the shop'})).toBeNull();
    expect(within(screen.getByRole('region',{name:'A2'})).queryByRole('button',{name:'At the café'})).toBeNull();
  });
  it('opens a grey A2 activity and starts its A2 task without changing a preference',async()=>{
    const task={...shopScenario,target_level:'A2'};
    const fetch=vi.fn((url:string,_init?:RequestInit)=>response(url.includes('/scenarios') ? catalogue : url.includes('/options') ? {...options,scenario:task} : url.endsWith('/connect') ? {sdp:'v=0 answer'} : {...saved,scenario:task}));
    vi.stubGlobal('fetch',fetch);const {getUserMedia}=fakeMedia();render(<LiveConversation />);
    const button=await scenarioButton('At the shop','A2');
    expect(button.hasAttribute('disabled')).toBe(false);
    fireEvent.click(button);
    await screen.findByRole('heading',{name:'A notebook for class'});
    expect(fetch.mock.calls.some(([url])=>url.endsWith('/options?scenario_id=shop&level=A2'))).toBe(true);
    expect(getUserMedia).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button',{name:/Start talking/}));
    await vi.waitFor(()=>expect(fetch.mock.calls.some(([url])=>url.endsWith('/connect'))).toBe(true));
    expect(JSON.parse(fetch.mock.calls.find(([url])=>url==='/api/v1/live-conversations')![1]?.body as string).target_level).toBe('A2');
    expect(fetch.mock.calls.some(([url])=>url.includes('/progression/preferences'))).toBe(false);
  });
  it('uses the separate live endpoint and starts one peer',async()=>{
    const fetch=setup();const {events,getUserMedia}=fakeMedia();render(<LiveConversation />);
    await chooseCafe();
    fireEvent.click(await screen.findByRole('button',{name:/Start talking/}));
    await vi.waitFor(()=>expect(fetch.mock.calls.some(([url])=>url.endsWith('/connect'))).toBe(true));
    events.onmessage({data:JSON.stringify({type:'session.started',event_id:'start'})});
    expect(await screen.findByText('The conversation is live')).toBeTruthy();
    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(window.location.hash).toBe('#speaking/live-one');
    expect(fetch.mock.calls.some(([url])=>url==='/api/v1/conversations')).toBe(false);
    const greeting=JSON.parse(events.send.mock.calls[0][0]);
    expect(greeting.type).toBe('session.instructions.append');
    expect(greeting.content).toContain('только по-русски');
    expect(greeting.content).toContain('Здравствуйте! Что будете пить: чай или кофе?');
  });
  it('mutes the actual microphone and ends without an extra rating page',async()=>{
    setup();const {track,events}=fakeMedia();render(<LiveConversation />);
    await chooseCafe();
    fireEvent.click(await screen.findByRole('button',{name:/Start talking/}));
    await vi.waitFor(()=>expect(events.onmessage).toBeTruthy());
    await vi.waitFor(()=>expect(track.stop).not.toHaveBeenCalled());
    // Wait until signalling has attached the event handler.
    await new Promise(resolve=>setTimeout(resolve,0));
    events.onmessage({data:JSON.stringify({type:'session.started'})});
    fireEvent.click(await screen.findByRole('button',{name:'Mute microphone'}));expect(track.enabled).toBe(false);
    fireEvent.click(screen.getByRole('button',{name:'End conversation'}));
    events.onmessage({data:JSON.stringify({type:'session.closed'})});
    await screen.findByText('Your conversation is saved.');expect(track.stop).toHaveBeenCalled();
    fireEvent.click(screen.getByRole('link',{name:/Try another conversation/}));
    expect(await scenarioButton('At the café')).toBeTruthy();
    expect(screen.queryByRole('button',{name:/Start talking/})).toBeNull();
    expect(window.location.hash).toBe('#speaking');
  });
  it('releases microphone permission that arrives after navigating away',async()=>{
    setup();const {getUserMedia,microphone,track}=fakeMedia();let grant:(value:unknown)=>void=()=>{};
    getUserMedia.mockImplementation(()=>new Promise(resolve=>{grant=resolve;}));
    const view=render(<LiveConversation />);await chooseCafe();fireEvent.click(await screen.findByRole('button',{name:/Start talking/}));
    await vi.waitFor(()=>expect(getUserMedia).toHaveBeenCalled());view.unmount();grant(microphone);
    await vi.waitFor(()=>expect(track.stop).toHaveBeenCalled());
  });
  it('opening a saved session does not request microphone or reconnect a provider',async()=>{
    const fetch=setup({...saved,state:'completed',captions:[{type:'session.output_transcript.delta',event_id:'a',delta:'Здравствуйте!',start_ms:1,end_ms:500}]});
    const {getUserMedia}=fakeMedia();render(<LiveConversation sessionId="live-one" />);
    await screen.findByText('Здравствуйте!');expect(getUserMedia).not.toHaveBeenCalled();
    expect(fetch.mock.calls.some(([url])=>url.endsWith('/connect'))).toBe(false);
  });
  it('preserves original Russian in notes and never shows a numeric language score',async()=>{
    setup({...saved,state:'completed',recordings:[{id:'r',ordinal:1,state:'ready',audio_url:'/private/r.wav',sample_count:24000,sample_rate:24000,retryable:false,
      transcript:{text:'Я хочу чай без сахар.'},assessment:{communication:'Your order was understandable.',uncertainty:'',corrections:[{original:'без сахар',replacement:'без сахара',explanation:'Use the genitive after без.'}]}}]});
    render(<LiveConversation sessionId="live-one" />);
    await screen.findByText('Я хочу чай без сахар.');expect(screen.getByText('без сахара')).toBeTruthy();
    expect(screen.getByLabelText('Your recording 1').getAttribute('src')).toBe('/private/r.wav');
    expect(screen.queryByText(/Grammar score|Fluency score|Elo/)).toBeNull();
  });
  it('uses the saved seed for the brief, menu and actual spoken opening',async()=>{
    const fetch=setup({...saved,scenario});const {events}=fakeMedia();render(<LiveConversation />);
    await chooseCafe();
    fireEvent.click(await screen.findByRole('button',{name:/Start talking/}));
    await vi.waitFor(()=>expect(fetch.mock.calls.some(([url])=>url.endsWith('/connect'))).toBe(true));
    expect(await screen.findByRole('heading',{name:'Time to warm up'})).toBeTruthy();
    expect(screen.getByText('Ask for no sugar')).toBeTruthy();
    expect(screen.getByText('90 ₽')).toBeTruthy();expect(screen.queryByText('100 ₽')).toBeNull();
    expect(screen.getByText('Tea')).toBeTruthy();expect(screen.getByText('Cocoa')).toBeTruthy();
    events.onmessage({data:JSON.stringify({type:'session.started',event_id:'start'})});
    expect(JSON.parse(events.send.mock.calls[0][0]).content).toContain(scenario.opening);
    expect(JSON.parse(events.send.mock.calls[0][0]).content).not.toContain('Что будете пить: чай или кофе?');
  });
  it('shows the exact seeded brief before microphone access and starts that seed',async()=>{
    const fetch=vi.fn((url:string,_init?:RequestInit)=>response(url.includes('/scenarios') ? catalogue : url.includes('/options') ? {...options,scenario} : url.endsWith('/connect') ? {sdp:'v=0 answer'} : {...saved,scenario}));
    vi.stubGlobal('fetch',fetch);const {getUserMedia}=fakeMedia();render(<LiveConversation />);
    await chooseCafe();
    expect(await screen.findByRole('heading',{name:'Time to warm up'})).toBeTruthy();
    expect(screen.getByText('Ask for no sugar')).toBeTruthy();expect(screen.getByText('90 ₽')).toBeTruthy();
    expect(getUserMedia).not.toHaveBeenCalled();
    expect(fetch.mock.calls.some(([url])=>url==='/api/v1/live-conversations')).toBe(false);
    fireEvent.click(screen.getByRole('button',{name:/Start talking/}));
    await vi.waitFor(()=>expect(fetch.mock.calls.some(([url])=>url==='/api/v1/live-conversations')).toBe(true));
    const startRequest=fetch.mock.calls.find(([url])=>url==='/api/v1/live-conversations')!;
    expect(JSON.parse(startRequest[1]?.body as string).scenario_seed).toBe(scenario.seed);
  });
  it('refreshes the task without creating a session or requesting the microphone',async()=>{
    const next={...scenario,seed:'cafe-takeaway-v1',title:'Something to take away',opening:'Здравствуйте! Что вам приготовить?'};
    const fetch=vi.fn((url:string,_init?:RequestInit)=>response(url.includes('/scenarios') ? catalogue : {...options,scenario:url.includes('exclude_seed=') ? next : scenario}));
    vi.stubGlobal('fetch',fetch);const {getUserMedia}=fakeMedia();render(<LiveConversation />);
    await chooseCafe();
    fireEvent.click(screen.getByRole('button',{name:'Another situation'}));
    expect(await screen.findByRole('heading',{name:'Something to take away'})).toBeTruthy();
    expect(fetch.mock.calls.some(([url])=>url.endsWith(`/options?scenario_id=cafe&level=A1&exclude_seed=${scenario.seed}`))).toBe(true);
    expect(fetch.mock.calls.every(([,init])=>!init?.method || init.method==='GET')).toBe(true);
    expect(getUserMedia).not.toHaveBeenCalled();
  });
  it('shows saved grammar, fluency and task feedback before captions without regrading',async()=>{
    const fetch=setup({...saved,state:'completed',scenario,end_reason:'task_complete',recordings:[{...recording,assessment:{communication:'Old excerpt note',uncertainty:'',corrections:[]}}],
      review:{state:'ready',error:null,retryable:false,report},captions:[{type:'session.output_transcript.delta',delta:'Всего доброго!',start_ms:10,end_ms:1000}]});
    const {getUserMedia}=fakeMedia();render(<LiveConversation sessionId="live-one" />);
    expect(await screen.findByText('Conversation finished.')).toBeTruthy();
    const feedback=screen.getByRole('heading',{name:'How you got on'}).closest('section')!;
    const captions=screen.getByLabelText('Conversation captions');
    expect(feedback.compareDocumentPosition(captions)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByText('Task & reference').closest('details')?.open).toBe(false);
    expect(screen.queryByText('КАФЕ')).toBeNull();
    const nextCall=screen.getByRole('link',{name:/Try another conversation/});
    expect(nextCall.closest('.live-feedback')).toBe(feedback);
    expect(screen.getByLabelText('Grammar').compareDocumentPosition(nextCall)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByLabelText('Grammar').textContent).toContain('3 / 5');
    expect(screen.getByLabelText('Fluency').textContent).toContain('4 / 5');
    expect(screen.getAllByText('Done')).toHaveLength(2);
    expect(screen.getByText('Still to try')).toBeTruthy();
    expect(screen.getByText(report.summary)).toBeTruthy();expect(screen.getByText(report.next_step)).toBeTruthy();
    expect(screen.getByText('Original recordings').closest('details')?.open).toBe(false);
    expect(screen.getByText('What the review heard').closest('details')?.open).toBe(false);
    expect(screen.queryByText('Old excerpt note')).toBeNull();
    expect(getUserMedia).not.toHaveBeenCalled();
    expect(fetch.mock.calls.some(([url])=>url.endsWith('/review'))).toBe(false);
  });
  it('reopens a saved shop review from its snapshot without loading the café or a new catalogue',async()=>{
    const fetch=setup({...saved,state:'completed',scenario_id:'shop',scenario:shopScenario,end_reason:'task_complete',recordings:[recording],
      review:{state:'ready',error:null,retryable:false,report:{...report,goals:[{id:'notebook',status:'completed',evidence:['тетрадь']}]}},
      captions:[{type:'session.output_transcript.delta',delta:'Спасибо за покупку!',start_ms:1,end_ms:500}]});
    const {getUserMedia}=fakeMedia();render(<LiveConversation sessionId="live-one" />);
    await screen.findByRole('heading',{name:'A notebook for class'});
    expect(screen.getByRole('heading',{name:'Your task'})).toBeTruthy();
    expect(screen.getByText('Shop assistant')).toBeTruthy();expect(screen.getByLabelText('Shopping list')).toBeTruthy();
    expect(screen.queryByText(/Your café task|café menu|Café worker/)).toBeNull();
    expect(screen.getByLabelText('Grammar').textContent).toContain('3 / 5');
    expect(fetch.mock.calls.some(([url])=>url.includes('/options') || url.includes('/scenarios') || url.endsWith('/review'))).toBe(false);
    expect(getUserMedia).not.toHaveBeenCalled();
  });
  it.each(['insufficient','unclear'])('does not invent scores when speech is %s',async speech_status=>{
    setup({...saved,state:'completed',scenario,recordings:[recording],review:{state:'ready',error:null,retryable:false,report:{...report,speech_status,
      grammar:{score:null,reason:'There is too little clear Russian to judge.',evidence:[]},fluency:{score:null,reason:'Try a slightly longer reply next time.',evidence:[]}}}});
    render(<LiveConversation sessionId="live-one" />);
    await screen.findByRole('heading',{name:'How you got on'});
    expect(screen.getAllByText(speech_status==='unclear'?'Not enough clear speech':'Not enough speech')).toHaveLength(2);
    expect(screen.queryByText(/\/ 5/)).toBeNull();
    expect(screen.getByText('Try a slightly longer reply next time.')).toBeTruthy();
  });
  it('only requests a legacy review when the learner clicks',async()=>{
    const fetch=setup({...saved,state:'completed',recordings:[recording]});render(<LiveConversation sessionId="live-one" />);
    const button=await screen.findByRole('button',{name:'Get speaking feedback'});
    expect(fetch.mock.calls.some(([url])=>url.endsWith('/review'))).toBe(false);
    fireEvent.click(button);
    await vi.waitFor(()=>expect(fetch.mock.calls.filter(([url])=>url==='/api/v1/live-conversations/live-one/review')).toHaveLength(1));
  });
  it('allows an explicit retry of failed feedback without restarting the call',async()=>{
    const value={...saved,state:'completed',recordings:[recording],review:{state:'failed',error:'Audio review unavailable.',retryable:true,report:null}};
    const fetch=setup(value);const {getUserMedia}=fakeMedia();render(<LiveConversation sessionId="live-one" />);
    fireEvent.click(await screen.findByRole('button',{name:'Try feedback again'}));
    await vi.waitFor(()=>expect(fetch.mock.calls.some(([url])=>url.endsWith('/review'))).toBe(true));
    expect(getUserMedia).not.toHaveBeenCalled();expect(screen.getByText('Audio review unavailable.')).toBeTruthy();
  });
  it.each(['queued','not_yet_queued'])('polls a new %s review without requesting another paid review',async initial=>{
    vi.useFakeTimers();
    let review:unknown=initial==='queued' ? {state:'queued',error:null,retryable:false,report:null} : null;
    const fetch=vi.fn((url:string)=>response(url.endsWith('/options') ? options : {...saved,state:'completed',scenario,recordings:[recording],review}));
    vi.stubGlobal('fetch',fetch);render(<LiveConversation sessionId="live-one" />);
    await vi.waitFor(()=>expect(screen.getByRole('heading',{name:'How you got on'})).toBeTruthy());
    if (initial==='queued') expect(screen.getByText('Listening back to your conversation…')).toBeTruthy();
    review={state:'ready',error:null,retryable:false,report};
    await vi.advanceTimersByTimeAsync(2500);
    expect(screen.getByText(report.summary)).toBeTruthy();
    expect(fetch.mock.calls.some(([url])=>url.endsWith('/review'))).toBe(false);
  });
  it('shows Russian task labels and feedback controls',async()=>{
    setup({...saved,state:'completed',scenario,recordings:[recording],review:{state:'ready',error:null,retryable:false,report}});
    render(<LiveConversation sessionId="live-one" language="ru" />);
    expect(await screen.findByRole('heading',{name:'Пора согреться'})).toBeTruthy();
    expect(screen.getByRole('heading',{name:'Как прошёл разговор'})).toBeTruthy();
    expect(screen.getByLabelText('Грамматика')).toBeTruthy();
    expect(screen.getAllByText('Попросите без сахара')).toHaveLength(2);
    expect(screen.queryByText('Ask for no sugar')).toBeNull();
  });
});

describe('WebRTC lifecycle',()=>{
  it('cleans up tracks and reports a failed signalling request',async()=>{
    setup();const {track}=fakeMedia();vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('Offline')));
    const connection=new LiveConnection('id',{status:vi.fn(),caption:vi.fn(),error:vi.fn(),playbackBlocked:vi.fn()});
    await expect(connection.start()).rejects.toThrow('Offline');expect(track.stop).toHaveBeenCalled();
  });
  it('keeps overlapping, late transcript fragments and their exact whitespace',()=>{
    const fragments:Caption[]=[
      {type:'session.input_transcript.delta',event_id:'u1',delta:'Я хочу',start_ms:100,end_ms:200},
      {type:'session.output_transcript.delta',event_id:'a1',delta:'Да?',start_ms:150,end_ms:250},
      {type:'session.input_transcript.delta',event_id:'u3',delta:' чай.',start_ms:400,end_ms:500},
      {type:'session.input_transcript.delta',event_id:'u2',delta:'... нет,',start_ms:250,end_ms:350},
    ];
    const rows=captionRows(fragments);expect(rows).toHaveLength(2);
    expect(rows[0].id).toBe('u1');expect(rows[0].text).toBe('Я хочу... нет, чай.');expect(rows[1].text).toBe('Да?');
  });
});

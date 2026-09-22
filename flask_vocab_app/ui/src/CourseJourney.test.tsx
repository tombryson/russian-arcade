import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/preact';
import {CourseJourney,type CourseData,type CourseAttempt} from './CourseJourney';
import type {ProgressionData} from './Progression';
const course=(patch:Partial<CourseData>={}):CourseData=>({version:1,profile_id:'learner',band:'A1',unlocked_levels:['A1'],current_chapter_id:'first',progress:.2,completed:false,chapters:Array.from({length:4},(_,index)=>({id:index===0 ? 'first' : `chapter-${index+1}`,number:index+1,title:['A small message','The market','A new address','Your original letter'][index],title_ru:'Короткое сообщение',intro:index===0 ? 'Meet Barsik’s helpers. Your original letter stays sealed.' : 'The next part of your journey.',intro_ru:'Познакомьтесь с помощниками Барсика.',status:index===0 ? 'practice' : 'locked',progress:index===0 ? .2 : 0,activity_count:0,required_activity_count:2,last_attempt_id:null,objectives:[{en:'Understand a short greeting.',ru:'Понять короткое приветствие.'}],preparation:[{topic_id:'greetings',title:'Say hello',title_ru:'Приветствия',explanation:'Use this phrase to introduce yourself.',explanation_ru:'Так можно представиться.',examples:[{ru:'Меня зовут Анна.',en:'My name is Anna.'}]}],topics:[{id:'greetings',title:'Greetings',title_ru:'Приветствия',completed:false,successful_tasks:1,required_tasks:2,links:[{activity:'reading',label:'Read a greeting',label_ru:'Читать приветствие',href:'/reading?topic=greetings&difficulty=A1'}]}]})),...patch});
const attempt=(patch:Partial<CourseAttempt>={}):CourseAttempt=>({id:'attempt-1',chapter_id:'first',chapter_number:1,title:'A small message',title_ru:'Короткое сообщение',letter:'Привет, Барсик! Меня зовут Анна.',letter_title:'A note for Barsik',letter_title_ru:'Записка для Барсика',glossary:[{ru:'привет',en:'hello'}],listening:{audio_url:'/static/audio/course/first.mp3'},questions:[{id:'read',kind:'reading',prompt:'Who wrote this message?',prompt_ru:'Кто написал сообщение?',choices:[{id:'anna',text:'Анна'},{id:'misha',text:'Миша'}]},{id:'listen',kind:'listening',prompt:'When is the meeting?',prompt_ru:'Когда встреча?',choices:[{id:'three',text:'В три часа'},{id:'four',text:'В четыре часа'}]},{id:'reply',kind:'response',prompt:'Choose your reply.',prompt_ru:'Выберите ответ.',choices:[{id:'yes',text:'Хорошо, спасибо!'},{id:'no',text:'До свидания!'}]}],status:'active',support_used:false,listened:false,course:course(),...patch});
const progression=(profile='learner')=>({data:{profile_id:profile,course:course({profile_id:profile})} as ProgressionData,error:'',loading:false,refresh:vi.fn()});
const result=(passed=true):CourseAttempt=>attempt({status:passed ? 'passed' : 'retry',listened:true,result:{score:passed ? 3 : 2,total:3,passed,feedback:[{question_id:'read',correct:true,answer:'anna',explanation:'Anna signs the message.',explanation_ru:'Анна подписала сообщение.'},{question_id:'listen',correct:passed,answer:'four',explanation:'The recording changes the meeting to four.',explanation_ru:'В записи встреча перенесена на четыре.'},{question_id:'reply',correct:true,answer:'yes',explanation:'Thank the helper.',explanation_ru:'Поблагодарите помощника.'}]}});
function respond(value:unknown,ok=true) {return {ok,json:async()=>value};}
function mockServer(handler:(url:string,body:Record<string,unknown>|undefined)=>unknown=()=>course()) {
  const fetch=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
    const value=await handler(String(input),options?.body ? JSON.parse(String(options.body)) : undefined);
    return respond(value);
  });vi.stubGlobal('fetch',fetch);return fetch;
}
async function selectAnswers() {
  fireEvent.click(await screen.findByRole('radio',{name:'Анна'}));fireEvent.click(screen.getByRole('radio',{name:'В четыре часа'}));fireEvent.click(screen.getByRole('radio',{name:'Хорошо, спасибо!'}));
}
beforeEach(()=>sessionStorage.clear());afterEach(()=>vi.unstubAllGlobals());
describe('Guided chapter journey',()=>{
  it('shows four chapters, honest locks and easy practice entry without opening the original letter',async()=>{
    mockServer();render(<CourseJourney progression={progression()}/>);
    await screen.findByRole('heading',{name:'A letter to discover'});
    expect(screen.getAllByText('Chapter 1 of 4 · In practice')).toHaveLength(2);
    expect(screen.getAllByText(/Coming next/)).toHaveLength(3);
    expect(screen.getByRole('link',{name:'Continue chapter →'}).getAttribute('href')).toBe('#journey/chapter/first');
    expect(screen.getByRole('link',{name:'Choose practice level'}).getAttribute('href')).toBe('/curriculum');
    expect(screen.getByRole('link',{name:'Browse all practice activities →'})).toBeTruthy();
    expect(screen.queryByText('Привет, Барсик! Меня зовут Анна.')).toBeNull();
  });
  it('teaches the topic and offers explicit early test-out with a stable request ID on retry',async()=>{
    let fail=true;const fetch=mockServer((url)=>{if (url.endsWith('/checkpoint')) {if(fail) throw new Error('Connection lost');return attempt();}return course();});
    render(<CourseJourney chapterId="first" progression={progression()}/>);
    expect(await screen.findByText('Use this phrase to introduce yourself.')).toBeTruthy();
    expect(screen.getByText('Меня зовут Анна.')).toBeTruthy();expect(screen.getByRole('link',{name:'Read a greeting →'}).getAttribute('href')).toContain('topic=greetings');
    fireEvent.click(screen.getByRole('button',{name:'Test out of this chapter →'}));await screen.findByRole('alert');
    fail=false;fireEvent.click(screen.getByRole('button',{name:'Test out of this chapter →'}));
    await waitFor(()=>expect(window.location.hash).toBe('#journey/checkpoint/attempt-1'));
    const writes=fetch.mock.calls.filter(([,options])=>options?.method==='POST');expect(writes).toHaveLength(2);
    const first=JSON.parse(String(writes[0][1]?.body));expect(first.challenge).toBe(true);expect(JSON.parse(String(writes[1][1]?.body))).toEqual(first);
  });
  it('offers a normal checkpoint once ready and stops checkpoint entry for a locked chapter',async()=>{
    const ready=course();ready.chapters[0].status='ready';mockServer(()=>ready);
    const {rerender}=render(<CourseJourney chapterId="first" progression={progression()}/>);
    expect(await screen.findByRole('button',{name:'Start checkpoint →'})).toBeTruthy();expect(screen.queryByRole('button',{name:/Test out/})).toBeNull();
    rerender(<CourseJourney chapterId="chapter-2" progression={progression()}/>);
    await screen.findByText('Pass the previous chapter’s checkpoint to continue. You can practise any time.');expect(screen.queryByRole('button',{name:'Start checkpoint →'})).toBeNull();
  });

  it('explains when completed topic work still needs a second activity',async()=>{
    const current=course();current.chapters[0].activity_count=1;current.chapters[0].topics[0].completed=true;
    mockServer(()=>current);render(<CourseJourney chapterId="first" progression={progression()}/>);
    expect(await screen.findByText(/Complete two successful tasks for each topic, using at least two activities/)).toBeTruthy();
    expect(screen.getByText(/1\/2 activities used/)).toBeTruthy();
    expect(screen.getByText(/Try another activity, such as Writing or Speaking/)).toBeTruthy();
  });
  it('shows honest A1 completion and available A2 practice',async()=>{
    mockServer(()=>course({completed:true,unlocked_levels:['A1','A2']}));render(<CourseJourney progression={progression()}/>);
    await screen.findByRole('heading',{name:'Your letter has arrived'});expect(screen.getByText(/A2 practice is now available/)).toBeTruthy();expect(screen.queryByText(/A2 journey/)).toBeNull();expect(screen.getByRole('link',{name:'Explore A2 practice →'}).getAttribute('href')).toBe('/curriculum#level-A2');
  });
});
describe('Chapter checkpoints',()=>{
  it('shows the passage before questions, accessible choices and bundled audio without listening credit on load',async()=>{
    let current=attempt();const fetch=mockServer((url)=>{if(url.endsWith('/listened')) current={...current,listened:true};return current;});
    const {container}=render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);
    const text=await screen.findByText('Привет, Барсик! Меня зовут Анна.');const question=screen.getByRole('group',{name:'1. Who wrote this message?'});
    expect(text.compareDocumentPosition(question)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByText('Useful words')).toBeTruthy();expect(fetch.mock.calls.every(([,options])=>options?.method==='GET')).toBe(true);
    const audio=screen.getByLabelText('Checkpoint recording');expect(audio.getAttribute('preload')).toBe('none');expect(audio.hasAttribute('autoplay')).toBe(false);
    expect(container.querySelector('.course-correction')).toBeNull();expect(screen.queryByText('The recording changes the meeting to four.')).toBeNull();
    await selectAnswers();expect((screen.getByRole('button',{name:'Check my answers'}) as HTMLButtonElement).disabled).toBe(true);
    fireEvent(audio,new Event('ended'));await screen.findByText('✓ Recording heard. You can replay it.');
    expect((screen.getByRole('button',{name:'Check my answers'}) as HTMLButtonElement).disabled).toBe(false);
    expect(fetch.mock.calls.filter(([url])=>String(url).endsWith('/listened'))).toHaveLength(1);
  });

  it('saves listening completion when the audio ends while a hint is loading',async()=>{
    let release:((value:CourseAttempt)=>void)|undefined;
    const fetch=mockServer((url)=>url.endsWith('/support') ? new Promise<CourseAttempt>(resolve=>{release=resolve;}) : attempt({listened:url.endsWith('/listened'),support_used:url.endsWith('/listened')}));
    render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);
    fireEvent.click((await screen.findAllByRole('button',{name:'Get a hint · practice only'}))[0]);
    fireEvent(screen.getByLabelText('Checkpoint recording'),new Event('ended'));
    release!(attempt({support_used:true}));
    await screen.findByText('✓ Recording heard. You can replay it.');
    expect(fetch.mock.calls.filter(([url])=>String(url).endsWith('/listened'))).toHaveLength(1);
  });
  it('reveals hints and the transcript only through server support and explains the practice-only consequence',async()=>{
    let current=attempt();const fetch=mockServer((url,body)=>{if(url.endsWith('/support')) {current={...current,support_used:true};if(body?.kind==='hint') current={...current,questions:current.questions.map(q=>q.id===body.question_id ? {...q,hint:'Look at the signature.',hint_ru:'Посмотрите подпись.'} : q)};else current={...current,listening:{...current.listening,transcript:'Встреча в четыре часа.'}};}return current;});
    render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);
    fireEvent.click((await screen.findAllByRole('button',{name:'Get a hint · practice only'}))[0]);await screen.findByText('Look at the signature.');
    expect(screen.getByText(/Support used: this is a practice attempt/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Read transcript · practice only'}));await screen.findByText('Встреча в четыре часа.');
    const bodies=fetch.mock.calls.filter(([url])=>String(url).endsWith('/support')).map(([,options])=>JSON.parse(String(options?.body)));
    expect(bodies).toEqual([{kind:'hint',question_id:'read'},{kind:'transcript'}]);
  });
  it('submits all choices once and freezes the saved response with useful corrections and retry',async()=>{
    const fetch=mockServer(url=>url.endsWith('/answer') ? result(false) : attempt({listened:true}));
    render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);await selectAnswers();
    const submit=screen.getByRole('button',{name:'Check my answers'});fireEvent.click(submit);fireEvent.click(submit);
    await screen.findByRole('heading',{name:'A little more practice'});expect(screen.getByText('The recording changes the meeting to four.')).toBeTruthy();
    expect((screen.getByRole('radio',{name:'Анна'}) as HTMLInputElement).closest('fieldset')?.disabled).toBe(true);
    expect(screen.getByRole('button',{name:'Try a different checkpoint →'})).toBeTruthy();expect(screen.queryByRole('button',{name:'Check my answers'})).toBeNull();
    const writes=fetch.mock.calls.filter(([url])=>String(url).endsWith('/answer'));expect(writes).toHaveLength(1);expect(JSON.parse(String(writes[0][1]?.body)).answers).toEqual({read:'anna',listen:'four',reply:'yes'});
    expect(sessionStorage.length).toBe(0);
  });


  it('shows corrections without repeated hints and focuses only a newly saved result',async()=>{
    const saved=result(false);saved.questions=saved.questions.map(question=>({...question,hint:'Read this again before answering.',hint_ru:'Прочитайте ещё раз.'}));
    let completed=false;mockServer(url=>{if (url.endsWith('/answer')) completed=true;return completed ? saved : attempt({listened:true});});
    const previousScroll=HTMLElement.prototype.scrollIntoView;const scroll=vi.fn();HTMLElement.prototype.scrollIntoView=scroll;
    try {
      const first=render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);await selectAnswers();
      fireEvent.click(screen.getByRole('button',{name:'Check my answers'}));
      const summary=await screen.findByRole('region',{name:'Checkpoint result'});
      await waitFor(()=>expect(document.activeElement).toBe(summary));expect(scroll).toHaveBeenCalledOnce();
      expect(screen.queryByText('Read this again before answering.')).toBeNull();
      expect(screen.getByText('The recording changes the meeting to four.')).toBeTruthy();first.unmount();
      render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);
      const reopened=await screen.findByRole('region',{name:'Checkpoint result'});
      expect(document.activeElement).not.toBe(reopened);expect(scroll).toHaveBeenCalledOnce();
    } finally {HTMLElement.prototype.scrollIntoView=previousScroll;}
  });
  it('restores submitted choices on a saved result and explains an essential detail miss',async()=>{
    const saved=result(false);saved.result!.score=3;saved.result!.essential_passed=false;
    saved.result!.feedback=saved.result!.feedback.map(item=>({...item,selected_answer:item.question_id==='listen' ? 'three' : item.answer}));
    mockServer(()=>saved);render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);
    expect((await screen.findByRole('radio',{name:'В три часа'}) as HTMLInputElement).checked).toBe(true);
    expect((screen.getByRole('radio',{name:'В четыре часа'}) as HTMLInputElement).checked).toBe(false);
    expect(screen.getByText('One key detail needs another look. Review the corrections and try again.')).toBeTruthy();
    expect(screen.getByText('The recording changes the meeting to four.')).toBeTruthy();
  });
  it('holds submitted answers after an uncertain save and retries the identical submission',async()=>{
    let fail=true;const fetch=mockServer(url=>{if(url.endsWith('/answer')) {if(fail) throw new Error('Offline');return result();}return attempt({listened:true});});
    render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);await selectAnswers();fireEvent.click(screen.getByRole('button',{name:'Check my answers'}));
    await screen.findByRole('alert');expect((screen.getByRole('radio',{name:'Миша'}) as HTMLInputElement).closest('fieldset')?.disabled).toBe(true);
    fail=false;fireEvent.click(screen.getByRole('button',{name:'Retry saving answers'}));await screen.findByRole('heading',{name:'Chapter passed'});
    const writes=fetch.mock.calls.filter(([url])=>String(url).endsWith('/answer'));expect(writes).toHaveLength(2);expect(writes[0][1]?.body).toBe(writes[1][1]?.body);
  });
  it('restores the learner’s draft on return and removes it when another learner takes over',async()=>{
    let profile='learner';mockServer(()=>attempt({course:course({profile_id:profile})}));
    const first=render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);fireEvent.click(await screen.findByRole('radio',{name:'Анна'}));first.unmount();
    const second=render(<CourseJourney attemptId="attempt-1" progression={progression()}/>);expect((await screen.findByRole('radio',{name:'Анна'}) as HTMLInputElement).checked).toBe(true);
    profile='another';second.rerender(<CourseJourney attemptId="attempt-1" progression={progression('another')}/>);
    await waitFor(()=>expect((screen.getByRole('radio',{name:'Анна'}) as HTMLInputElement).checked).toBe(false));expect(sessionStorage.length).toBe(0);
  });
  it('does not show another profile’s course and offers retry after a load error',async()=>{
    mockServer(()=>course({profile_id:'another'}));render(<CourseJourney progression={progression()}/>);
    expect(await screen.findByRole('alert')).toBeTruthy();expect(screen.queryByRole('heading',{name:'A letter to discover'})).toBeNull();expect(screen.getByRole('button',{name:'Try again'})).toBeTruthy();
  });
});

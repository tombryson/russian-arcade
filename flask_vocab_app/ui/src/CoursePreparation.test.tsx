import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/preact';
import {CoursePreparation,type CoursePractice} from './CoursePreparation';
import type {ProgressionState} from './Progression';
const progression={data:{profile_id:'p',course:{release_id:'a1-journey-v2'}},refresh:vi.fn(),loading:false,error:''} as unknown as ProgressionState;
const practice=():CoursePractice=>({id:'practice-1',profile_id:'p',section_id:'home',status:'active',completed_count:0,total_count:1,current_item:{id:'item-1',target_id:'target-1',title:'A family member',title_ru:'Член семьи',stage:'learn',teaching:{explanation:'Use моя before сестра.',explanation_ru:'Перед словом «сестра» употребляем «моя».',example_ru:'Это моя сестра.',example_en:'This is my sister.'},question:{prompt:'Which phrase fits?',prompt_ru:'Какой вариант подходит?',choices:[{id:'right',text:'Моя сестра'},{id:'wrong',text:'Мой сестра'}]},hint:null,feedback:null,listened:false,transcript:null},coverage:{required_count:1,prepared_count:0,ready:false,targets:[]}});
function serve(handler:(url:string,body:any)=>unknown){const fetch=vi.fn(async(url:string,options?:RequestInit)=>({ok:true,json:async()=>handler(url,options?.body?JSON.parse(String(options.body)):undefined)}));vi.stubGlobal('fetch',fetch);return fetch;}
beforeEach(()=>{window.location.hash='';});afterEach(()=>vi.unstubAllGlobals());
describe('Milestone target practice',()=>{
  it('teaches before recall, checks a real choice and returns to the same milestone',async()=>{
    let value=practice();const fetch=serve(url=>{
      if(url.endsWith('/learn'))value={...value,current_item:{...value.current_item!,stage:'question'}};
      if(url.endsWith('/answer'))value={...value,current_item:{...value.current_item!,stage:'feedback',feedback:{correct:true,answer:'right',explanation:'Сестра takes моя.',explanation_ru:'Перед словом «сестра» стоит «моя».'}}};
      if(url.endsWith('/next'))value={...value,status:'completed',current_item:null,completed_count:1};return value;
    });render(<CoursePreparation practiceId="practice-1" progression={progression}/>);
    await screen.findByText('Use моя before сестра.');expect(screen.queryByRole('radio')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Try it →'}));fireEvent.click(await screen.findByRole('radio',{name:'Моя сестра'}));fireEvent.click(screen.getByRole('button',{name:'Check answer'}));
    expect(await screen.findByText('That’s right.')).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'Finish practice →'}));
    await screen.findByRole('heading',{name:'Practice saved'});expect(screen.getByRole('link',{name:'Continue the milestone →'}).getAttribute('href')).toBe('#journey/chapter/home');
    const commands=fetch.mock.calls.filter(([,options])=>options?.method==='POST');expect(commands.map(([url])=>url.split('/').at(-1))).toEqual(['learn','answer','next']);
    expect(JSON.parse(String(commands[1][1]?.body))).toMatchObject({item_id:'item-1',choice_id:'right'});
  });
  it('starts or resumes section practice with a stable request across an uncertain start',async()=>{
    let fail=true;const fetch=vi.fn(async(_url:string,_options?:RequestInit)=>{if(fail)throw new Error('Offline');return{ok:true,json:async()=>practice()};});vi.stubGlobal('fetch',fetch);
    render(<CoursePreparation sectionId="home" progression={progression}/>);await screen.findByRole('alert');fail=false;fireEvent.click(screen.getByRole('button',{name:'Try again'}));
    await waitFor(()=>expect(window.location.hash).toBe('#journey/practice/practice-1'));
    expect(fetch.mock.calls[0][1]?.body).toBe(fetch.mock.calls[1][1]?.body);expect(JSON.parse(String(fetch.mock.calls[0][1]?.body)).release_id).toBe('a1-journey-v2');
  });
  it('does not expose another learner’s saved practice',async()=>{
    serve(()=>({...practice(),profile_id:'other'}));render(<CoursePreparation practiceId="practice-1" progression={progression}/>);
    await screen.findByRole('alert');expect(screen.queryByText('Use моя before сестра.')).toBeNull();
  });
  it('requires the listening clip or optional transcript before checking',async()=>{
    let value=practice();value.current_item={...value.current_item!,stage:'question',question:{...value.current_item!.question!,audio_url:'/static/audio/example.mp3'}};
    serve(url=>{if(url.endsWith('/listened'))value={...value,current_item:{...value.current_item!,listened:true}};return value;});
    render(<CoursePreparation practiceId="practice-1" progression={progression}/>);fireEvent.click(await screen.findByRole('radio',{name:'Моя сестра'}));expect((screen.getByRole('button',{name:'Check answer'}) as HTMLButtonElement).disabled).toBe(true);
    fireEvent(screen.getByLabelText('Practice recording'),new Event('ended'));await waitFor(()=>expect((screen.getByRole('button',{name:'Check answer'}) as HTMLButtonElement).disabled).toBe(false));
  });
});

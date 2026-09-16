import {afterEach,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/preact';
import {GameStudyActions} from './GameStudyActions';
afterEach(()=>vi.unstubAllGlobals());
it('opens the ordinary generator only after an explicit click',async()=>{
  const fetch=vi.fn(async(_url:string,_request?:RequestInit)=>({ok:true,json:async()=>({id:'same-native-batch'})}));vi.stubGlobal('fetch',fetch);
  render(<GameStudyActions sessionId="saved-game"/>);expect(fetch).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button',{name:'Practise these words'}));
  await waitFor(()=>expect(location.hash).toBe('#generate/same-native-batch'));
  expect(fetch.mock.calls[0][0]).toBe('/api/v1/games/sessions/saved-game/flashcards');
});
it('keeps a failed request retryable without navigating to a broken set',async()=>{
  const fetch=vi.fn().mockResolvedValueOnce({ok:false,json:async()=>({error:{code:'temporarily_unavailable',message:'Please try again.'}})})
    .mockResolvedValue({ok:true,json:async()=>({id:'recovered-batch'})});vi.stubGlobal('fetch',fetch);
  render(<GameStudyActions sessionId="saved-game"/>);
  fireEvent.click(screen.getByRole('button',{name:'Practise these words'}));
  expect((await screen.findByRole('alert')).textContent).toContain('Please try again.');
  fireEvent.click(screen.getByRole('button',{name:'Practise these words'}));
  await waitFor(()=>expect(location.hash).toBe('#generate/recovered-batch'));
});
it('stops a stale profile from opening another learner’s batch',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,json:async()=>({error:{code:'profile_changed',message:'Your profile changed.'}})})));
  render(<GameStudyActions sessionId="saved-game"/>);
  fireEvent.click(screen.getByRole('button',{name:'Practise these words'}));
  expect((await screen.findByRole('alert')).textContent).toContain('Your profile changed.');
  expect(screen.getByRole('button',{name:'Practise these words'}).hasAttribute('disabled')).toBe(true);
  expect(screen.getByRole('link',{name:'Choose your profile'}).getAttribute('href')).toBe('/post/profiles');
});

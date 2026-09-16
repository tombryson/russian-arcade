import {useEffect,useRef,useState} from 'preact/hooks';
import {api,ApiError} from './learning-api';

export function GameStudyActions({sessionId}:{sessionId:string}) {
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[blocked,setBlocked]=useState(false);
  const pending=useRef(false),mounted=useRef(true);
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
  async function open() {
    if(pending.current)return;
    pending.current=true;setBusy(true);setError('');
    try {
      const result=await api<{id:string}>(`/api/v1/games/sessions/${encodeURIComponent(sessionId)}/flashcards`,{});
      if(!result||typeof result.id!=='string'||!result.id)throw new Error('Your flashcards could not open. Please try again.');
      if(mounted.current)window.location.hash=`generate/${encodeURIComponent(result.id)}`;
    } catch(cause) {
      if(mounted.current){setError(cause instanceof Error?cause.message:'Your flashcards could not open. Please try again.');setBlocked(cause instanceof ApiError&&['profile_changed','forbidden','profile_required','not_found'].includes(cause.code));}
    } finally {pending.current=false;if(mounted.current)setBusy(false);}
  }
  return <div class="journey-game-study"><p>Keep these words fresh with flashcards, pictures and Russian audio.</p>
    <button class="text-link" disabled={busy||blocked} onClick={()=>void open()}>{busy?'Opening flashcards…':'Practise these words'} <span aria-hidden="true">→</span></button>
    {error&&<p role="alert">{error}{blocked&&<> <a href="/post/profiles">Choose your profile</a></>}</p>}
  </div>;
}

import {useEffect,useRef,useState} from 'preact/hooks';
import {ApiError} from './learning-api';
import {AudioClue} from './GameAudio';
import {ClozeBoard,DetectiveBoard,GameArtwork,gamePresentation,LetterBackBoard,MailSortBoard,PairsBoard,RadioBoard,VocabularyPicture} from './GameBoards';
import {GamePreparation} from './GamePreparation';
import {RadioBroadcast,RadioQuestions} from './RadioBroadcast';
import {GameWords} from './GameWords';
import {GameWordSource} from './GameWordSource';
import {GameStudyActions} from './GameStudyActions';
import {getGame,getGames,saveGame,startGame,type GameAction,type GameBoard,type GameCatalogueState,type GameObject,type GameOptions,type GameRound,type GameState,type GameSummary,type Heading,type JourneyGameId,type MapPosition} from './journey-games-api';
import './styles/journey-games.css';

const arrows:Record<string,string>={left:'↶',straight:'↑',right:'↷'};
const moveNames:Record<string,string>={left:'Turn left',straight:'Go straight',right:'Turn right'};
const headingNames:Record<Heading,string>={north:'up',east:'right',south:'down',west:'left'};
const directions:Heading[]=['north','east','south','west'];
const blockedCodes=['profile_changed','locked','profile_required','learner_required','csrf_failed','unauthorized','not_found'];
function GameError({message,blocked=false,retry,busy=false}:{message:string;blocked?:boolean;retry:()=>void;busy?:boolean}) {
  return <div class="journey-game-error" role="alert"><p>{message}</p>{blocked ? <a class="text-link" href="/post/#activities">Reopen activities</a> : <button class="text-link" disabled={busy} onClick={retry}>Try again</button>}</div>;
}
function useCatalogue() {
  const [state,setState]=useState<GameCatalogueState>();
  const [error,setError]=useState(''),[revision,setRevision]=useState(0);
  useEffect(()=>{const abort=new AbortController();setError('');void getGames(abort.signal).then(value=>{if(!abort.signal.aborted)setState(value);}).catch(cause=>{if(!abort.signal.aborted){setState(undefined);setError(cause instanceof Error ? cause.message : 'Your games could not load.');}});return()=>abort.abort();},[revision]);
  return {state,error,retry:()=>setRevision(value=>value+1)};
}
function GameCard({game,discovery=false}:{game:GameSummary;discovery?:boolean}) {
  return <article class={`journey-game-card game-${game.id}${game.unlocked ? '' : ' is-locked'}`}>
    <div class="journey-game-card-art" aria-hidden="true"><GameArtwork gameId={game.id}/>{game.id==='directions' && <img src="/static/images/barsik-running-v1.webp" alt=""/>}</div>
    <div class="journey-game-card-copy"><p class="kicker">{!game.unlocked ? 'Coming up' : game.new ? 'New game unlocked' : 'Play again'}</p><h3>{game.title}</h3><p>{game.description}</p>
      {game.unlocked ? <a class={discovery ? 'cta' : 'text-link'} href={game.active_session_id ? `#games/session/${game.active_session_id}` : `#games/${game.id}`}>{game.active_session_id ? 'Continue playing' : 'Play'} <span aria-hidden="true">→</span></a> : <p class="journey-game-lock">Finish <a href={game.lesson_href}>{game.lesson_title}</a> to unlock.</p>}
    </div>
  </article>;
}
export function GameUnlocks({lessonId}:{lessonId?:string}) {
  const {state,error,retry}=useCatalogue();
  const games=state?.games.filter(game=>game.unlocked && (!lessonId || game.lesson_id===lessonId)) ?? [];
  if(!games.length && !error)return null;
  return <section class={`journey-game-unlocks${!lessonId?' is-collection':''}`} aria-label="Games from this lesson">{!lessonId&&games.length>0?<><h2>Your unlocked games</h2><div class="journey-game-collection">{games.map(game=><a key={game.id} href={game.active_session_id?`#games/session/${game.active_session_id}`:`#games/${game.id}`}><GameArtwork gameId={game.id}/><span>{game.title}<small>{game.active_session_id?'Continue playing':'Play again'}</small></span><span aria-hidden="true">→</span></a>)}</div></>:games.map(game=><GameCard key={game.id} game={game} discovery/>)}{games.length>0 && <p class="journey-game-keep">You can find {games.length===1 ? 'this game' : 'these games'} in <a href="#activities">Activities</a> whenever you want to play again.</p>}{error && <GameError message={error} retry={retry}/>}</section>;
}
export function GameCatalogue({context='activities'}:{context?:'activities'|'journey'}) {
  const {state,error,retry}=useCatalogue();
  const unlocked=state?.games.filter(game=>game.unlocked)??[],upcoming=state?.games.filter(game=>!game.unlocked)??[];
  return <section class="journey-games-catalogue" aria-label="Games to discover"><div class="journey-games-section-head"><p class="kicker">Explore and practise</p><h2>{context==='journey' ? 'Games along the way' : 'Games to discover'}</h2><p>Build on words you know, meet new ones and try a different way to practise.</p></div>
    {state ? <>{unlocked.length>0&&<div class="journey-game-grid">{unlocked.map(game=><GameCard key={game.id} game={game}/>)}</div>}{upcoming.length>0&&<details class="journey-games-upcoming" open={unlocked.length===0||upcoming.length<3}><summary>Coming up · {upcoming.length} {upcoming.length===1?'game':'games'}</summary><ul>{upcoming.map(game=><li key={game.id}><GameArtwork gameId={game.id}/><div><strong>{game.title}</strong><p>Finish <a href={game.lesson_href}>{game.lesson_title}</a> to unlock.</p></div></li>)}</ul></details>}</> : !error && <p role="status">Opening your games…</p>}{error && <GameError message={error} retry={retry}/>}</section>;
}

function ObjectArt({object}:{object:GameObject}) {
  return <VocabularyPicture visual={object.visual==='letter'?'envelope':object.visual} image_url={object.image_url}/>;
}
function BagBoard({round,selected,onChange,disabled,expected}:{round:GameRound;selected:string[];onChange:(items:string[])=>void;disabled:boolean;expected?:string[]}) {
  const objects=round.objects ?? [];
  function toggle(id:string){if(selected.includes(id))onChange(selected.filter(item=>item!==id));else if(selected.length<round.max_choices)onChange([...selected,id]);}
  return <div class="journey-bag-board"><div class="journey-bag-shelf"><p class="journey-game-board-label">{expected ? 'What Barsik needed' : 'Picture cards'}</p><div class="journey-bag-objects">{objects.map(object=>{const packed=selected.includes(object.id),needed=expected?.includes(object.id),wrong=!!expected&&packed&&!needed;
    return <button key={object.id} class={`journey-bag-object${expected ? ' is-feedback' : packed ? ' is-packed' : ''}${needed ? ' is-needed' : wrong ? ' is-unneeded' : ''}`} aria-label={expected ? needed ? `Needed in the bag: ${object.label}` : wrong ? `Not needed: ${object.label}` : object.label : `${packed ? 'Remove' : 'Pack'} ${object.label}`} aria-pressed={packed} disabled={disabled || (!packed && selected.length>=round.max_choices)} onClick={()=>toggle(object.id)}><ObjectArt object={object}/><span class="journey-bag-select" aria-hidden="true">{expected ? needed ? '✓' : wrong ? '×' : '' : packed ? '✓' : '+'}</span></button>;
  })}</div></div>
    <div class="journey-bag-parcel"><p class="journey-game-board-label">Barsik’s bag <span>{selected.length} / {round.max_choices}</span></p><div class="journey-bag-handle" aria-hidden="true"/><div class="journey-bag-pocket" aria-label="Packed items">{selected.length ? selected.map(id=>{const object=objects.find(item=>item.id===id);return object && <button key={id} aria-label={`Take ${object.label} out of the bag`} disabled={disabled} onClick={()=>toggle(id)}><ObjectArt object={object}/>{expected && <span class={`journey-bag-result ${expected.includes(id) ? 'is-correct' : 'is-incorrect'}`} aria-label={expected.includes(id) ? 'Correct item' : 'Different item needed'}>{expected.includes(id) ? '✓' : '×'}</span>}</button>;}) : <p>Choose a picture<br/>to put it in the bag.</p>}</div><span class="journey-bag-buckle" aria-hidden="true"/></div>
  </div>;
}
export function traceRoute(board:GameBoard,moves:string[]):MapPosition[] {
  const path:MapPosition[]=[{...board.start}];
  for(const move of moves){const previous=path[path.length-1],turn=move==='left' ? -1 : move==='right' ? 1 : 0;const heading=directions[(directions.indexOf(previous.heading)+turn+4)%4];const x=previous.x+(heading==='east'?1:heading==='west'?-1:0),y=previous.y+(heading==='south'?1:heading==='north'?-1:0);path.push({x,y,heading});}
  return path;
}
function MapBoard({board,selected,onChange,disabled,limit,expected}:{board:GameBoard;selected:string[];onChange:(moves:string[])=>void;disabled:boolean;limit:number;expected?:string[]}) {
  const path=traceRoute(board,selected),current=path[path.length-1],expectedPath=expected ? traceRoute(board,expected) : null;
  const point=(p:MapPosition|{x:number;y:number})=>`${30+p.x*60},${30+p.y*60}`;
  const canMove=(move:string)=>{const destination=traceRoute(board,[...selected,move]).at(-1)!;return destination.x>=0&&destination.x<board.width&&destination.y>=0&&destination.y<board.height;};
  const angle=directions.indexOf(current.heading)*90,width=board.width*60,height=board.height*60;
  const streets=[...Array.from({length:board.height},(_,i)=>`M30 ${30+i*60}H${width-30}`),...Array.from({length:board.width},(_,i)=>`M${30+i*60} 30V${height-30}`)];
  return <div class="journey-map-board"><div class="journey-map-frame"><svg viewBox={`0 0 ${width} ${height}`} class="journey-street-map" role="img" aria-label={`Street map. Barsik is at column ${current.x+1}, row ${current.y+1}, facing ${headingNames[current.heading]}. ${selected.length} of ${limit} moves planned.`}>
    <rect width={width} height={height} rx="20" fill="#e5e6c9"/>
    {Array.from({length:board.height-1},(_,y)=>Array.from({length:board.width-1},(_,x)=><g key={`${x}-${y}`} transform={`translate(${44+x*60} ${44+y*60})`}><rect width="32" height="32" rx="7" fill={(x+y)%3===0?'#b9c8a2':'#e7c499'}/>{(x+y)%3===0 ? <><circle cx="13" cy="12" r="8" fill="#779b77"/><circle cx="21" cy="23" r="6" fill="#779b77"/></> : <><path d="M7 12l9-6 9 6v14H7z" fill={(x+y)%2===0?'#c27858':'#8a9f9e'}/><path d="M6 12l10-7 10 7" fill="none" stroke="#5d6662" stroke-width="2"/><rect x="14" y="19" width="4" height="7" fill="#f7e9ce"/></>}</g>))}
    {streets.map((street,index)=><g key={index}><path d={street} fill="none" stroke="#faf5e7" stroke-width="18" stroke-linecap="round"/><path d={street} fill="none" stroke="#dfd8be" stroke-width="1.5" stroke-dasharray="2 7"/></g>)}
    {board.landmarks.filter(item=>item.image_url).map((item,index)=><g key={index} transform={`translate(${30+item.x*60} ${30+item.y*60})`}><title>{item.label??'Picture landmark'}</title><rect x="-23" y="-23" width="46" height="46" rx="5" fill="#fffaeb" stroke="#b9b28b" stroke-width="2"/><image href={item.image_url} x="-20" y="-20" width="40" height="40" preserveAspectRatio="xMidYMid slice"/></g>)}
    {expectedPath && <polyline points={expectedPath.map(point).join(' ')} fill="none" stroke="#51876c" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" opacity=".65" stroke-dasharray="3 10"/>}
    <circle cx={30+board.start.x*60} cy={30+board.start.y*60} r="8" fill="#fffdf3" stroke="#4f625d" stroke-width="2"/>
    {path.length>1 && <polyline points={path.map(point).join(' ')} fill="none" stroke="#b15e44" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>}
    {path.slice(1,-1).map((position,index)=><circle key={index} cx={30+position.x*60} cy={30+position.y*60} r="4" fill="#b15e44"/>)}
    <g class="journey-map-barsik" transform={`translate(${30+current.x*60} ${30+current.y*60})`}><circle r="17" fill="#fcf5df" stroke="#b15e44" stroke-width="2"/><path d="M-5 -23l5-6 5 6" fill="none" stroke="#32494a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" transform={`rotate(${angle})`}/><image href="/static/images/barsik-running-v1.webp" x="-20" y="-15" width="40" height="30" transform={current.heading==='west'?'scale(-1 1)':undefined}/></g>
    {expectedPath && <g transform={`translate(${point(expectedPath.at(-1)!)})`}><circle r="23" fill="none" stroke="#51876c" stroke-width="3"/><g transform="translate(16 -18)"><circle r="8" fill="#51876c"/><path d="M-4 0l3 3 5-6" fill="none" stroke="#fffdf3" stroke-width="2"/></g></g>}
  </svg><p class="journey-map-facing">Barsik is facing <strong>{headingNames[current.heading]}</strong>. Each arrow moves him one street.</p></div>
    <div class="journey-map-controls"><p class="journey-game-board-label">Plan the route <span>{selected.length} / {limit}</span></p><div class="journey-map-route" aria-label="Your planned route">{selected.length ? selected.map((move,index)=><span key={index} aria-label={`${index+1}. ${moveNames[move]}`}>{arrows[move]}</span>) : <p>Your moves will appear here.</p>}</div><div class="journey-map-arrows">{['left','straight','right'].map(move=><button key={move} aria-label={moveNames[move]} title={moveNames[move]} disabled={disabled || selected.length>=limit || !canMove(move)} onClick={()=>onChange([...selected,move])}><span aria-hidden="true">{arrows[move]}</span><small>{move==='straight'?'Straight':move==='left'?'Left':'Right'}</small></button>)}</div><div class="journey-map-edit"><button class="text-link" disabled={disabled || !selected.length} onClick={()=>onChange(selected.slice(0,-1))}>Undo</button><button class="text-link" disabled={disabled || !selected.length} onClick={()=>onChange([])}>Start over</button></div><p class="journey-map-tip">Left and right follow the way Barsik is facing.</p>{expectedPath && <p class="journey-map-legend"><span aria-hidden="true"/>The dotted green line shows the route in the instructions.</p>}</div>
  </div>;
}

export function JourneyGame({gameId,sessionId,profileHref='/post/profiles'}:{gameId?:string;sessionId?:string;profileHref?:string}) {
  const [catalogue,setCatalogue]=useState<GameCatalogueState>(),[state,setState]=useState<GameState>();
  const [options,setOptions]=useState<GameOptions>({source:'vocabulary',rounds:5});
  const [selected,setSelected]=useState<string[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[blocked,setBlocked]=useState(false);
  const mounted=useRef(true),pending=useRef(false),requestId=useRef(''),heading=useRef<HTMLHeadingElement>(null),last=useRef<{action:'load'|'start'|GameAction;body?:unknown}>({action:'load'}),owner=useRef<string|null|undefined>(undefined);
  const entry=catalogue?.games.find(game=>game.id===gameId),round=state?.round;
  useEffect(()=>{mounted.current=true;void load();return()=>{mounted.current=false;};},[]);
  useEffect(()=>{heading.current?.focus({preventScroll:true});},[state?.phase,state?.round_index]);
  function accept(next:GameState,preserveDraft=false){if(!mounted.current)return;if(owner.current!==undefined && owner.current!==next.profile_id)throw new ApiError('Your profile changed. Reopen this page before continuing.','profile_changed');owner.current=next.profile_id;setState(next);if(!preserveDraft)setSelected(next.result?.answer ?? []);}
  function report(cause:unknown){if(!mounted.current)return;const inaccessible=cause instanceof ApiError&&blockedCodes.includes(cause.code);setBlocked(inaccessible);if(inaccessible){setState(undefined);setCatalogue(undefined);setSelected([]);}setError(cause instanceof Error ? cause.message : 'Your game could not be saved.');}
  async function load(){if(pending.current)return;pending.current=true;setBusy(true);setError('');setBlocked(false);last.current={action:'load'};try{if(sessionId)accept(await getGame(sessionId));else{const next=await getGames();if(mounted.current){setCatalogue(next);owner.current=next.profile_id;if(!next.games.some(game=>game.id===gameId))throw new ApiError('This game could not be found.','not_found');}}}catch(cause){report(cause);}finally{pending.current=false;if(mounted.current)setBusy(false);}}
  async function start(){if(pending.current)return;pending.current=true;setBusy(true);setError('');last.current={action:'start'};if(!requestId.current)requestId.current=crypto.randomUUID();try{const next=await startGame(gameId!,requestId.current,options,!!entry?.active_session_id);accept(next);if(mounted.current)window.location.hash=`games/session/${next.id}`;}catch(cause){report(cause);}finally{pending.current=false;if(mounted.current)setBusy(false);}}
  async function save(action:GameAction,body:unknown={}){if(pending.current||!state)return;pending.current=true;setBusy(true);setError('');last.current={action,body};try{let next:GameState;try{next=await saveGame(state.id,action,body);}catch(cause){if(cause instanceof ApiError&&['answer_already_saved','wrong_round'].includes(cause.code))next=await getGame(state.id);else throw cause;}accept(next,['hint','listen','transcript'].includes(action)&&next.round?.id===round?.id&&next.phase==='play');if(mounted.current&&action==='continue'&&next.phase==='ready'){last.current={action:'complete',body:{}};next=await saveGame(next.id,'complete');accept(next);}}catch(cause){report(cause);}finally{pending.current=false;if(mounted.current)setBusy(false);}}
  function retry(){const request=last.current;if(request.action==='load')void load();else if(request.action==='start')void start();else void save(request.action,request.body);}
  const title=state?.title ?? entry?.title ?? 'A game with Barsik';
  const currentGame=(state?.game_id??entry?.id??gameId??'pack-bag') as JourneyGameId;
  const basePresentation=gamePresentation[currentGame]??gamePresentation['pack-bag'];
  const vocabularyReply=currentGame==='letter-back'&&(round?.audio_required||['vocabulary','lesson'].includes(state?.source?.kind??''));
  const broadcast=state?.broadcast,radioProgramme=currentGame==='radio'&&(!state||!!broadcast);
  const presentation=radioProgramme?{...basePresentation,instructions:'Tune in to a short Russian radio programme, then answer four questions about what you heard.',check:'Check answer',help:'Choose the answer that matches the programme.',correct:'That’s right.',finish:'Thanks for listening.',summary:'You’ve listened to a Russian programme and checked what you understood.'}:vocabularyReply?{...basePresentation,check:'Check the message',correct:'That’s the message.',finish:'Message complete.'}:basePresentation;
  const answerUncertain=!!error&&last.current.action==='answer';
  const interactionBlocked=busy||answerUncertain||state?.phase!=='play';
  const expected=state?.phase==='feedback'?state.result?.expected_answer:undefined;
  const radioSupported=!!round&&(round.support?.transcript||round.clues.every(clue=>round.support?.listened_audio_keys.includes(clue.audio_key)));
  const needsListening=!broadcast&&(currentGame==='radio'||!!round?.audio_required);
  const completeDraft=!!round&&selected.length>0&&(!['pairs','mailbox-sort','letter-back'].includes(currentGame)||selected.length===round.max_choices)&&(!needsListening||radioSupported);
  const boardProps=round?{round,selected,onChange:setSelected,disabled:interactionBlocked,expected}:null;
  function boardContent() {
    if(!round||!boardProps)return null;
    switch(currentGame) {
      case 'pack-bag':return <BagBoard {...boardProps}/>;
      case 'directions':return round.board&&<MapBoard board={round.board} selected={selected} onChange={setSelected} disabled={interactionBlocked} limit={round.max_choices} expected={expected}/>;
      case 'pairs':return <PairsBoard key={round.id} {...boardProps}/>;
      case 'mailbox-sort':return <MailSortBoard key={round.id} {...boardProps}/>;
      case 'missing-stamp':return <ClozeBoard {...boardProps}/>;
      case 'radio':return broadcast?<RadioQuestions {...boardProps}/>:<RadioBoard key={round.id} {...boardProps} onHeard={key=>save('listen',{round_id:round.id,audio_key:key})} onTranscript={()=>void save('transcript',{round_id:round.id})}/>;
      case 'detective':return <DetectiveBoard key={round.id} {...boardProps}/>;
      case 'letter-back':return <LetterBackBoard key={round.id} {...boardProps} onHeard={key=>save('listen',{round_id:round.id,audio_key:key})} onTranscript={()=>void save('transcript',{round_id:round.id})}/>;
    }
  }
  const vocabularySource=state?.source?.kind==='vocabulary'||state?.source?.href==='#words';
  const emptySource=!radioProgramme&&currentGame!=='directions'&&options.source==='lesson'&&!!catalogue?.sources&&(catalogue.sources.lessons.find(item=>item.id===options.lesson_id)?.count??0)===0;
  const playing=!!state&&['play','feedback','listening'].includes(state.phase);
  return <section class={`page journey-game game-player-${currentGame}${playing?' is-playing':''}`}>
    <div class="lesson-head"><a class="text-link" href="#activities">All activities</a>{state?.source&&state.source.kind!=='route'&&<a class="text-link" href={state.source.href}>{vocabularySource?'Back to vocabulary':'Back to the lesson'}</a>}</div>
    {!playing&&<p class="kicker">{state?.phase==='completed'?'Game complete':'Play with Barsik'}</p>}
    <header class="journey-game-heading"><h1 ref={heading} tabIndex={-1}>{title}</h1>
      {playing&&round&&<div class="journey-game-round-head"><p class="journey-game-round-count">{broadcast?'Question':'Round'} {state.round_index+1} of {state.total_rounds}</p><div class="journey-game-round-dots" aria-hidden="true">{Array.from({length:state.total_rounds},(_,index)=><span key={index} class={index<=state.round_index?'is-current':''}/>)}</div></div>}
    </header>
    {!state&&entry&&<div class="journey-game-intro"><div class="journey-game-intro-art" aria-hidden="true"><GameArtwork gameId={currentGame}/></div><div><p class="intro">{presentation.instructions}</p>{entry.active_session_id&&<a class="cta game-continue-saved" href={`#games/session/${entry.active_session_id}`}>Continue saved game <span aria-hidden="true">→</span></a>}{currentGame!=='directions'&&<GameWordSource broadcast={radioProgramme} sources={catalogue?.sources} options={options} disabled={busy} onChange={value=>{setOptions(value);requestId.current='';setError('');}}/>}<p class="quiet">{radioProgramme?'About a minute · 4 questions':`${options.rounds} rounds.`}</p>{emptySource&&<p class="game-source-empty">{options.source==='vocabulary'?<>Add words to <a href="#words">your vocabulary</a> to build this game.</>:'This lesson has no saved words yet. Choose another word source.'}</p>}{entry.unlocked?<button class="cta" disabled={busy||emptySource} onClick={()=>void start()}>{busy?'Opening your game…':entry.active_session_id?radioProgramme?'Make another programme':'Start a new game':radioProgramme?'Tune in':'Let’s play'} <span aria-hidden="true">→</span></button>:<p class="journey-game-locked-message">This game unlocks after <a href={entry.lesson_href}>{entry.lesson_title}</a>.</p>}</div></div>}
    {broadcast&&state?.phase!=='preparing'&&<RadioBroadcast compact={state?.phase!=='listening'} sessionId={state!.id} broadcast={broadcast} busy={busy} onHeard={()=>save('listen',{round_id:'broadcast',audio_key:broadcast.audio_key})} onTranscript={()=>void save('transcript',{round_id:'broadcast'})}/>}
    {state?.phase==='listening'&&broadcast?<div class="radio-start-questions"><p>{broadcast.listened?'Ready to see what you caught?':broadcast.transcript?'Read or listen, then try the questions.':'Listen to the programme first. The questions come next.'}</p><button class="cta" disabled={busy||(!broadcast.listened&&!broadcast.transcript)} onClick={()=>void save('quiz')}>{busy?'Opening questions…':'Answer the questions'} <span aria-hidden="true">→</span></button></div>:state?.phase==='preparing'?sessionId?<GamePreparation key={state.id} initial={state} onReady={accept} onBlocked={report}/>:<p role="status">Opening your saved game…</p>:state?.phase==='completed'?<div class="journey-game-completed">
      <div class="journey-game-completed-art" aria-hidden="true"><GameArtwork gameId={currentGame}/><span>✓</span></div><h2>{presentation.finish}</h2><p>{presentation.summary}</p>{broadcast&&state.summary&&<p class="radio-quiz-score"><strong>{state.summary.correct_rounds} of {state.summary.total_rounds}</strong> questions correct.</p>}
      {!state.profile_id?<p class="quiet">Your practice is saved on this device. <a href={profileHref}>Create a profile to keep it.</a></p>:state.reward&&state.reward.amount>0?<p class="journey-game-reward"><strong>{state.reward.awarded_now?'+':''}{state.reward.amount} Lingocoins</strong> · {state.reward.awarded_now?'Added to your balance':'Already saved'}</p>:<p class="quiet">{state.reward?.reason==='already_rewarded'?'You’ve already earned coins for this game today. You can keep playing.':state.reward?.reason==='daily_cap'?'Your game is saved. You’ve earned today’s activity coins, and you can keep playing.':'Your practice is saved. No extra coins were added this time.'}</p>}
      <div class="action-row"><a class="cta" href={state.source.href}>{state.source.kind==='route'?'All activities':vocabularySource?'Back to vocabulary':state.source.kind==='lesson'?'Back to the lesson':'Back to First steps'} <span aria-hidden="true">→</span></a><a class="text-link" href={`#games/${state.game_id}`}>Play again</a><a class="text-link" href="#activities">Choose another activity</a></div>
      {!!state.words?.length&&<GameWords sessionId={state.id} words={state.words}/>}
      {state.profile_id&&state.study_available&&<GameStudyActions sessionId={state.id}/>}
    </div>:state&&round?<>
      <div class="journey-game-instruction"><h2 lang={broadcast?'ru':undefined}>{round.prompt}</h2>
        {!['radio','detective'].includes(currentGame)&&!round.audio_required&&<div class="journey-game-clues">{round.clues.map((clue,index)=><AudioClue key={`${round.id}-${index}-${clue.audio_key}`} text={clue.text} audioKey={clue.audio_key}/>)}</div>}
        {round.hint?<p class="journey-game-hint" role="status">{round.hint}</p>:state.phase==='play'&&!needsListening&&<button class="text-link" disabled={busy||answerUncertain} onClick={()=>void save('hint',{round_id:round.id})}>Show a hint</button>}
      </div>
      <div class="journey-game-stage">{boardContent()}</div>
      {state.phase==='feedback'&&state.result?<div class={`journey-game-feedback ${state.result.correct?'is-correct':''}`} role="status"><div><h2>{state.result.correct?presentation.correct:'Let’s take another look.'}</h2><p>{state.result.feedback}</p>{state.result.answer_audio&&state.result.answer_audio.length>0&&<div class="game-answer-recordings"><p class="journey-game-board-label">Listen to the complete message</p>{state.result.answer_audio.map((clue,index)=><AudioClue key={`${round.id}-answer-${index}`} text={clue.text} audioKey={clue.audio_key} hideText label={state.result!.answer_audio!.length>1?`Listen to phrase ${index+1}`:'Listen to the complete message'}/>)}</div>}</div><button class="cta" disabled={busy} onClick={()=>void save('continue',{round_id:round.id})}>{busy?'Saving…':state.round_index+1===state.total_rounds?broadcast?'Finish programme':'Finish game':broadcast?'Next question':'Next round'} <span aria-hidden="true">→</span></button></div>:<div class="journey-game-submit"><p>{presentation.help}{needsListening&&!radioSupported&&<> Listen or reveal the text before checking.</>}</p><button class="cta" disabled={busy||answerUncertain||!completeDraft} onClick={()=>void save('answer',{round_id:round.id,answer:selected})}>{busy?'Saving…':presentation.check} <span aria-hidden="true">→</span></button></div>}
    </>:state?.phase==='ready'?<div class="journey-game-completed"><p>You’ve played all {state.total_rounds} rounds.</p><button class="cta" disabled={busy} onClick={()=>void save('complete')}>{busy?'Saving…':broadcast?'Finish programme':'Finish game'}</button></div>:!entry&&!error&&<p class="journey-game-loading" role="status">Opening your game…</p>}
    {error&&<GameError message={error} blocked={blocked} retry={retry} busy={busy}/>}
  </section>;
}

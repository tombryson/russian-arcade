import {api} from './learning-api';

export type JourneyGameId='pack-bag'|'directions'|'pairs'|'mailbox-sort'|'missing-stamp'|'radio'|'detective'|'letter-back';
export type GameSummary={id:JourneyGameId;title:string;description:string;lesson_id:string;lesson_title:string;lesson_href:string;unlocked:boolean;new:boolean;active_session_id:string|null};
export type GameSources={word_count:number;form_count:number;topics:string[];lessons:{id:string;title:string;count:number}[]};
export type GameOptions={source:'vocabulary'|'lesson';lesson_id?:string;topic?:string;difficulty?:number;rounds:5|10};
export type GameCatalogueState={profile_id:string|null;games:GameSummary[];sources?:GameSources};
export type Heading='north'|'east'|'south'|'west';
export type MapPosition={x:number;y:number;heading:Heading};
export type GameBoard={width:number;height:number;start:MapPosition;landmarks:{x:number;y:number;visual:string;image_url?:string;label?:string}[]};
export type GameObject={id:string;visual:string;label:string;image_url?:string};
export type GameClue={text?:string;audio_key:string};
export type GameTextOption={id:string;text:string;audio_key?:string};
export type GameRound={id:string;mechanic?:string;prompt:string;clues:GameClue[];hint?:string;objects?:GameObject[];board?:GameBoard;max_choices:number;left?:GameTextOption[];right?:GameObject[];sentences?:GameTextOption[];bins?:{id:string;label:string;description?:string}[];sentence?:string;translation?:string;visual?:string;image_url?:string;audio_required?:boolean;choices?:{id:string;text?:string;visual?:string;label?:string;image_url?:string}[];destinations?:{id:string;visual:string;route:string[];label:string;image_url?:string}[];tiles?:GameTextOption[];support?:{listened_audio_keys:string[];transcript:boolean}};
export type GameBroadcast={title:string;audio_key:string;duration_seconds?:number;script?:string;listened:boolean;transcript:boolean};
export type GameWord={lemma:string;form:string;sentence?:string;translation?:string;target_meaning?:string;in_vocabulary?:boolean};
export type GameWordLookup={word:string;lemma:string|null;pos?:string|null;grammar?:Record<string,string>;word_id?:number|null;in_vocabulary:boolean;can_add:boolean;context?:string;translation?:string;meaning?:string;message?:string;dictionary_url?:string|null;choices:{lemma:string;pos?:string;label:string;word_id?:number|null;in_vocabulary:boolean;can_add:boolean;dictionary_url?:string}[];added?:boolean};
export type GameState={profile_id:string|null;id:string;game_id:JourneyGameId;title:string;phase:'preparing'|'listening'|'play'|'feedback'|'ready'|'completed';broadcast?:GameBroadcast;words?:GameWord[];summary?:{correct_rounds:number;total_rounds:number;matched:number;total:number};preparation?:{status:'pending'|'running'|'ready'|'failed';ready:number;total:number;stage:string;message:string;error?:string};round_index:number;total_rounds:number;round:GameRound|null;result:null|{answer:string[];correct:boolean;expected_answer:string[];feedback:string;path?:MapPosition[];score?:number;matched?:number;total?:number;answer_audio?:GameClue[]};reward:null|{amount:number;status:'credited'|'pending';awarded_now:boolean;reason?:'awarded'|'already_rewarded'|'daily_cap'|'profile_needed'};source:{lesson_id?:string;kind?:'vocabulary'|'lesson'|'first_steps'|'route';title:string;href:string};study_available?:boolean};
export type GameAction='hint'|'answer'|'continue'|'complete'|'listen'|'transcript'|'quiz';
export type GameAudio={status:'ready'|'pending'|'failed'|'unavailable';url?:string;message?:string};
export async function getGames(signal?:AbortSignal):Promise<GameCatalogueState> {
  const value=await api<GameCatalogueState>('/api/v1/games',undefined,signal);
  if(!value||!Array.isArray(value.games)||!value.games.every(game=>game&&typeof game.id==='string'&&typeof game.title==='string'&&typeof game.unlocked==='boolean'&&typeof game.lesson_href==='string'))throw new Error('Your games could not load. Please try again.');
  if(value.sources){const sources=value.sources;if(!Number.isFinite(sources.word_count)||!Number.isFinite(sources.form_count)||!Array.isArray(sources.topics)||!sources.topics.every(topic=>typeof topic==='string')||!Array.isArray(sources.lessons)||!sources.lessons.every(lesson=>lesson&&typeof lesson.id==='string'&&typeof lesson.title==='string'&&Number.isFinite(lesson.count)))throw new Error('Your word sources could not load. Please try again.');}
  return value;
}
export const startGame=(gameId:string,requestId:string,options:GameOptions={source:'vocabulary',rounds:5},newGame=false)=>api<GameState>(`/api/v1/games/${encodeURIComponent(gameId)}/start`,{request_id:requestId,options,...(newGame?{new_game:true}:{})});
export const prepareGame=(id:string,retry=false,signal?:AbortSignal)=>api<GameState>(`/api/v1/games/sessions/${encodeURIComponent(id)}/prepare`,retry?{retry:true}:{},signal);
export const getGame=(id:string,signal?:AbortSignal)=>api<GameState>(`/api/v1/games/sessions/${encodeURIComponent(id)}`,undefined,signal);
export const saveGame=(id:string,action:GameAction,body:unknown={})=>api<GameState>(`/api/v1/games/sessions/${encodeURIComponent(id)}/${action}`,body);
export const prepareGameAudio=(key:string)=>api<GameAudio>(`/api/v1/games/media/${encodeURIComponent(key)}/prepare`,{});
export const getGameAudio=(key:string,signal?:AbortSignal)=>api<GameAudio>(`/api/v1/games/media/${encodeURIComponent(key)}/status`,undefined,signal);
export const getGameWord=(id:string,word:string,signal?:AbortSignal)=>api<GameWordLookup>(`/api/v1/games/sessions/${encodeURIComponent(id)}/words?word=${encodeURIComponent(word)}`,undefined,signal);
export const addGameWord=(id:string,word:string,lemma:string,pos?:string)=>api<GameWordLookup>(`/api/v1/games/sessions/${encodeURIComponent(id)}/words`,{word,lemma,...(pos?{pos}:{})});

import {useGameLanguage} from './GameLocale';
import type {GameOptions, GameRound, SceneSlotResult} from './journey-games-api';
import './styles/scene-builder.css';

const topics = [
  ['location', 'Location', 'Местоположение', 'Prepositions and endings', 'Предлоги и окончания'],
  ['motion', 'Verbs of motion', 'Глаголы движения', 'Walking, travelling and arriving', 'Пешком, на транспорте, прибытие'],
  ['placement', 'Position and placement', 'Положение предметов', 'Lying, standing and putting', 'Лежит, стоит, положить, поставить'],
  ['agreement', 'Agreement', 'Согласование', 'Adjectives and noun endings', 'Прилагательные и окончания'],
  ['roles', 'Who does what?', 'Кто что делает?', 'Subjects and objects', 'Кто действует и на кого'],
  ['mixed', 'Mixed practice', 'Смешанная практика', 'Mix the five topics', 'Все пять тем'],
] as const;

export function SceneBuilderOptions({options, onChange, disabled}: {
  options: GameOptions; onChange: (options: GameOptions) => void; disabled: boolean;
}) {
  const ru=useGameLanguage()==='ru';
  return <div class="scene-options">
    <fieldset disabled={disabled}><legend>{ru?'Что будем практиковать?':'What would you like to practise?'}</legend>
      <div class="scene-topic-grid">{topics.map(([id,en,russian,detail,detailRu])=><button key={id} type="button" class="scene-topic" aria-label={ru?russian:en} aria-pressed={(options.grammar_focus??'location')===id} onClick={()=>onChange({...options,grammar_focus:id})}><strong>{ru?russian:en}</strong><span>{ru?detailRu:detail}</span></button>)}</div>
    </fieldset>
    <fieldset disabled={disabled} class="scene-length"><legend>{ru?'Длина игры':'Game length'}</legend>{([5,10] as const).map(rounds=><button type="button" key={rounds} aria-pressed={options.rounds===rounds} onClick={()=>onChange({...options,rounds})}>{rounds} {ru?'заданий':'rounds'}</button>)}</fieldset>
  </div>;
}

function SceneIllustration({scene, description}: {scene:string;description:string}) {
  const image=(name:string,className:string)=> <img src={`/static/images/scene-builder/${name}-v1.webp`} class={className} alt="" aria-hidden="true" draggable={false}/>;
  const location=scene.startsWith('cat-');
  const book=scene.startsWith('book-');
  const roles=scene==='girl-calls-boy'||scene==='boy-calls-girl';
  return <div class={`scene-illustration scene-${scene}`} role="img" aria-label={description}>
    <div class="scene-room-wall"/><div class="scene-room-floor"/>
    {location && <>{image('table','scene-table')}{image('cat','scene-cat')}</>}
    {book && <>{image('table','scene-table')}{image(scene==='book-upright'?'book-upright':'book','scene-book')}</>}
    {['walking','taxi','walking-away','taxi-moving','taxi-away','doorway-inside','courtyard-in','courtyard-out'].includes(scene)&&image(scene,'scene-travel')}
    {roles&&<svg viewBox="0 0 500 350" class="scene-people" aria-hidden="true">
      <g transform="translate(125 65)"><path d="M-37 82Q-52-10 0-10Q55-10 35 82" fill="#775044"/><circle cy="36" r="32" fill="#e6b590"/><path d="M-42 100Q0 61 42 100L57 190H-57Z" fill="#c88265"/><path d="M-22 191v54m44-54v54" stroke="#354d55" stroke-width="18" stroke-linecap="round"/><circle cx="-11" cy="33" r="3" fill="#35434a"/><circle cx="11" cy="33" r="3" fill="#35434a"/><path d="M-8 48q8 8 16 0" fill="none" stroke="#a55e4c" stroke-width="3"/></g>
      <g transform="translate(375 65)"><circle cy="36" r="32" fill="#e6b590"/><path d="M-33 26q-3-45 34-39q43 0 31 48L13 6-11 20z" fill="#694c40"/><path d="M-44 105Q0 66 44 105l10 79H-54Z" fill="#73989a"/><path d="M-22 188v56m44-56v56" stroke="#354d55" stroke-width="18" stroke-linecap="round"/><circle cx="-11" cy="33" r="3" fill="#35434a"/><circle cx="11" cy="33" r="3" fill="#35434a"/><path d="M-8 48q8 8 16 0" fill="none" stroke="#a55e4c" stroke-width="3"/></g>
      <g transform={scene==='boy-calls-girl'?'translate(500 0) scale(-1 1)':undefined}><path d="M177 112q65-49 126 0" fill="none" stroke="#a77840" stroke-width="5" stroke-dasharray="8 9"/><path d="m292 94 17 22-27 1" fill="none" stroke="#a77840" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><path d="m170 95 7-12m-22 9 1-13" stroke="#a77840" stroke-width="4" stroke-linecap="round"/></g>
      <text x="125" y="342" text-anchor="middle" fill="#3f5055" font-size="18">Анна</text><text x="375" y="342" text-anchor="middle" fill="#3f5055" font-size="18">Иван</text>
    </svg>}
  </div>;
}

export function SceneBuilder({round, selected, onChange, disabled, expected, slotResults}: {
  round:GameRound;selected:string[];onChange:(values:string[])=>void;disabled:boolean;expected?:string[];slotResults?:SceneSlotResult[];
}) {
  const ru=useGameLanguage()==='ru';
  const scene=round.scene_builder;
  if(!scene)return null;
  const checked=!!expected;
  const scenario=ru?scene.scenario_ru:scene.scenario;
  const chosenText=(index:number,values:string[])=>{
    const text=scene.slots[index].choices.find(choice=>choice.id===values[index])?.text??'';
    return index===0 && !scene.segments[0] ? text.charAt(0).toUpperCase()+text.slice(1) : text;
  };
  const completeSentence=expected?scene.segments.map((segment,index)=>segment+(index<scene.slots.length?chosenText(index,expected):'')).join(''):'';
  function choose(index:number,id:string) {
    const next=scene!.slots.map((_,i)=>selected[i]??'');
    next[index]=id;
    onChange(next);
  }
  return <div class="scene-builder">
    <figure class="scene-figure"><SceneIllustration scene={scene.scene} description={scenario}/><figcaption>{scenario}</figcaption></figure>
    <div class="scene-construction">
      <p class="scene-instruction">{ru?'Дополните предложение.':'Complete the sentence.'}</p>
      <div class="scene-sentence" lang="ru" aria-label={ru?'Ваше предложение':'Your sentence'}>{scene.segments.map((segment,index)=><span key={index}>{segment}{index<scene.slots.length&&<span class={`scene-blank${selected[index]?' is-filled':''}${checked?(selected[index]===expected[index]?' is-correct':' is-incorrect'):''}`} aria-label={!selected[index]?(ru?`Пропуск ${index+1}`:`Blank ${index+1}`):undefined}>{chosenText(index,selected)||'…'}</span>}</span>)}</div>
      <div class="scene-choice-banks">{scene.slots.map((slot,index)=>{
        const result=slotResults?.find(item=>item.id===slot.id);
        return <fieldset key={slot.id} class="scene-choice-bank" disabled={disabled}><legend><span class="scene-slot-number" aria-hidden="true">{index+1}</span>{ru?slot.label_ru:slot.label}</legend><div class="scene-choice-buttons">{slot.choices.map(choice=><button key={choice.id} type="button" lang="ru" aria-pressed={selected[index]===choice.id} class={`${selected[index]===choice.id?'is-selected ':''}${checked&&expected[index]===choice.id?'is-answer':''}`} onClick={()=>choose(index,choice.id)}>{choice.text}{checked&&expected[index]===choice.id&&<span aria-hidden="true"> ✓</span>}</button>)}</div>{result&&<p class={`scene-slot-feedback${result.correct?' is-correct':''}`}><span aria-hidden="true">{result.correct?'✓':'↪'} </span>{ru?result.explanation_ru:result.explanation}</p>}</fieldset>;
      })}</div>
      {checked&&<div class="scene-correct-sentence"><p>{ru?'Полное предложение':'The complete sentence'}</p><strong lang="ru">{completeSentence}</strong></div>}
    </div>
  </div>;
}

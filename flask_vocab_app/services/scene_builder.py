"""Authored scene contrasts, with independently checked sentence components.

These examples test a stated grammatical distinction. The caption provides
facts a still image cannot show (transport, repetition or completed action).
No vocabulary sampling or model call is involved in starting a session.
"""
import hashlib
import json
import random
import re

from flask import current_app

from repositories.learning_repository import LearningError, encoded, identifier, timestamp, transaction

VERSION = 'scene-builder-v1'
GAME = {'id': 'scene-builder', 'title': 'Describe the scene', 'lesson_id': 'bag',
        'lesson_title': 'What’s in the bag?',
        'description': 'Build Russian sentences about position, movement and who does what.'}
FAMILIES = ('location', 'motion', 'placement', 'agreement', 'roles')


def slot(identity, label, label_ru, choices):
    return {'id': identity, 'label': label, 'label_ru': label_ru,
            'choices': [{'id': identity + ':' + key, 'text': text} for key, text in choices]}


def item(identity, family, scene, scenario, scenario_ru, segments, slots, answers,
         translation, explanations, hint, hint_ru, word=None):
    expected = [part['id'] + ':' + answer for part, answer in zip(slots, answers)]
    sentence = segments[0]
    for position, (part, answer) in enumerate(zip(slots, expected)):
        sentence += next(choice['text'] for choice in part['choices'] if choice['id'] == answer) + segments[position + 1]
    sentence = sentence[0].upper() + sentence[1:]
    result = {'id': identity, 'mechanic': 'scene-builder', 'prompt': 'Build the sentence to describe the scene.',
              'clues': [], 'max_choices': len(slots), 'expected_answer': expected,
              'scene_builder': {'family': family, 'scene': scene, 'scenario': scenario, 'scenario_ru': scenario_ru,
                                'segments': segments, 'slots': slots},
              'hint': hint, 'hint_ru': hint_ru, 'feedback': sentence, 'translation': translation,
              'correct_sentence': sentence, 'slot_explanations': explanations,
              'answer_audio': [{'text': sentence, 'audio_key': hashlib.sha256(sentence.encode('utf-8')).hexdigest()}]}
    if word:
        lemma, form, pos, grammar, meaning = word
        result['vocabulary'] = {'lemma': lemma, 'form': form, 'pos': pos, 'grammar': grammar,
                                'sentence': sentence, 'translation': translation, 'target_meaning': meaning,
                                'source': {'kind': 'grammar', 'title': 'Describe the scene', 'url': '/#games/scene-builder'}}
    return result


def _locations():
    preps = slot('preposition', 'Position', 'Положение', [('on', 'на'), ('under', 'под'), ('behind', 'за'),
                 ('front', 'перед'), ('beside', 'рядом со'), ('above', 'над')])
    nouns = slot('noun', 'Noun ending', 'Форма существительного', [('base', 'стол'), ('prepositional', 'столе'), ('instrumental', 'столом')])
    rows = [('on', 'on', 'on top of', 'на поверхности', 'prepositional', 'loct'),
            ('under', 'under', 'underneath', 'ниже столешницы', 'instrumental', 'ablt'),
            ('beside', 'beside', 'beside', 'сбоку от', 'instrumental', 'ablt'),
            ('behind', 'behind', 'behind', 'с дальней стороны', 'instrumental', 'ablt'),
            ('in-front', 'front', 'in front of', 'с ближней стороны', 'instrumental', 'ablt')]
    result = []
    for scene, prep, english, russian, ending, case in rows:
        preposition_text = next(choice['text'] for choice in preps['choices'] if choice['id'] == 'preposition:' + prep)
        result.append(item('position-' + prep, 'location', 'cat-' + scene + '-table',
            f'Describe Barsik’s position relative to the table: he is {english} it.',
            f'Опишите положение Барсика относительно стола. Он {russian}{"." if prep == "under" else " стола."}',
            ['Барсик ', ' ', '.'], [preps, nouns], [prep, ending], f'Barsik is {english} the table.',
            [(f'Use «{preposition_text}» for this position.',
              'Выберите предлог, который соответствует положению кота.'),
             ('For a location with «на», use the prepositional form «столе».' if case == 'loct' else 'Here the preposition takes the instrumental form «столом».',
              'Для места после «на» нужен предложный падеж: «столе».' if case == 'loct' else 'Здесь нужен творительный падеж: «столом».')],
            'Describe where the cat is, then choose the noun ending required by that preposition.',
            'Опишите, где кот, затем выберите форму существительного после предлога.',
            ('стол', 'столе' if case == 'loct' else 'столом', 'NOUN', {'case': case, 'number': 'sing'}, 'table')))
    # Reverse the perspective without changing the picture. This checks the
    # relationship rather than memorisation of one image-to-button pairing.
    cat_preps = slot('preposition', 'Position', 'Положение', [('under', 'под'), ('behind', 'за'), ('front', 'перед'), ('beside', 'рядом с'), ('above', 'над')])
    cats = slot('noun', 'Noun ending', 'Форма существительного', [('base', 'кот'), ('genitive', 'кота'), ('instrumental', 'котом')])
    reverse = [('on', 'under', 'under the cat', 'ниже кота'), ('under', 'above', 'above the cat', 'выше кота'),
               ('beside', 'beside', 'beside the cat', 'сбоку от кота'), ('behind', 'front', 'in front of the cat', 'ближе к нам, чем кот'),
               ('in-front', 'behind', 'behind the cat', 'дальше от нас, чем кот')]
    for scene, prep, english, russian in reverse:
        result.append(item('reverse-position-' + prep, 'location', 'cat-' + scene + '-table',
            f'This time describe the table, not Barsik. The table is {english}.',
            f'Теперь опишите стол относительно кота. Стол {russian}.',
            ['Стол ', ' ', '.'], [cat_preps, cats], [prep, 'instrumental'], f'The table is {english}.',
            [('Describe the table’s position from the cat’s point of reference.', 'Опишите положение стола относительно кота.'),
             ('This preposition takes the instrumental: «котом».', 'После этого предлога нужен творительный падеж: «котом».')],
            'The sentence begins with the table. Reverse the relationship you see.',
            'Предложение начинается со слова «стол». Посмотрите на положение стола относительно кота.',
            ('кот', 'котом', 'NOUN', {'case': 'ablt', 'number': 'sing'}, 'cat')))
    return result


def _motions():
    present = slot('verb', 'Verb of motion', 'Глагол движения', [('walk-now','идёт'),('walk-usual','ходит'),('ride-now','едет'),('ride-usual','ездит')])
    arrival = slot('verb', 'Arrival or departure', 'Прибытие или отъезд', [('arrive-foot','пришёл'),('arrive-ride','приехал'),('leave-foot','ушёл'),('leave-ride','уехал')])
    boundary = slot('verb', 'Entering or leaving', 'Вход или выход', [('enter-foot','вошёл'),('exit-foot','вышел'),('enter-ride','въехал'),('exit-ride','выехал')])
    rows = [
        ('walk-now','walking','John is on foot, halfway to the café right now.','Джон сейчас на пути в кафе. Он пешком.',present,'walk-now',['Джон сейчас ', ' в кафе.'],'John is walking to the café now.','идти','идёт','Use «идёт» for one journey on foot happening now.','«Идёт» — одно направленное движение пешком сейчас.'),
        ('walk-habit','walking','John walks to the café every morning. Describe his routine.','Каждое утро Джон отправляется в кафе пешком. Это его привычка.',present,'walk-usual',['Джон каждое утро ', ' в кафе.'],'John walks to the café every morning.','ходить','ходит','Use «ходит» for a regular trip on foot.','«Ходит» подходит для регулярных походов пешком.'),
        ('ride-now','taxi-moving','John is in a moving taxi, halfway to the café right now.','Джон сейчас в такси на пути в кафе.',present,'ride-now',['Джон сейчас ', ' в кафе на такси.'],'John is going to the café by taxi now.','ехать','едет','Use «едет» for one journey by transport happening now.','«Едет» — одно направленное движение на транспорте сейчас.'),
        ('ride-habit','taxi-moving','John takes a taxi to the café every Friday. Describe his routine.','Каждую пятницу Джон добирается до кафе на такси.',present,'ride-usual',['Джон каждую пятницу ', ' в кафе на такси.'],'John goes to the café by taxi every Friday.','ездить','ездит','Use «ездит» for regular journeys by transport.','«Ездит» подходит для регулярных поездок.'),
        ('arrive-foot','walking','John walked from home and has just reached the café. Describe his arrival.','Джон добрался из дома до кафе пешком и уже здесь.',arrival,'arrive-foot',['Джон ', ' в кафе пешком.'],'John arrived at the café on foot.','прийти','пришёл','«Пришёл» means he arrived on foot.','«Пришёл» обозначает прибытие пешком.'),
        ('arrive-ride','taxi','John took a taxi and has just reached the café. Describe his arrival.','Джон добрался до кафе на такси и уже здесь.',arrival,'arrive-ride',['Джон ', ' в кафе на такси.'],'John arrived at the café by taxi.','приехать','приехал','«Приехал» means he arrived by transport.','«Приехал» обозначает прибытие на транспорте.'),
        ('leave-foot','walking-away','John has finished his coffee. He left the café on foot and is no longer there.','Кофе допит. Джона уже нет в кафе: он отправился домой пешком.',arrival,'leave-foot',['Джон ', ' из кафе пешком.'],'John left the café on foot.','уйти','ушёл','«Ушёл» means he left on foot.','«Ушёл» обозначает уход пешком.'),
        ('leave-ride','taxi-away','John has finished his coffee. His taxi took him away from the café.','Кофе допит. Джона уже нет в кафе: такси отвезло его домой.',arrival,'leave-ride',['Джон ', ' из кафе на такси.'],'John left the café by taxi.','уехать','уехал','«Уехал» means he left by transport.','«Уехал» обозначает отъезд на транспорте.'),
        ('enter-foot','doorway-inside','John was outside. He crossed the café doorway on foot and is now inside.','Сначала Джон был снаружи кафе. Он пересёк порог пешком и теперь внутри.',boundary,'enter-foot',['Джон ', ' в кафе.'],'John entered the café.','войти','вошёл','«Вошёл» describes crossing into a place on foot.','«Вошёл» — движение внутрь пешком.'),
        ('exit-foot','walking-away','John was inside the café. He crossed the doorway on foot and is now outside.','Сначала Джон был внутри кафе. Он пересёк порог пешком и теперь снаружи.',boundary,'exit-foot',['Джон ', ' из кафе.'],'John came out of the café.','выйти','вышел','«Вышел» describes crossing out of a place on foot.','«Вышел» — движение наружу пешком.'),
        ('enter-ride','courtyard-in','John’s taxi crossed the entrance into a courtyard. The car is now inside the courtyard.','Такси с Джоном пересекло ворота. Теперь машина внутри двора.',boundary,'enter-ride',['Джон ', ' во двор на такси.'],'John entered the courtyard by taxi.','въехать','въехал','«Въехал» describes entering a space by transport.','«Въехал» — движение внутрь на транспорте.'),
        ('exit-ride','courtyard-out','John’s taxi crossed the gate out of a courtyard. The car is now outside the courtyard.','Такси с Джоном пересекло ворота. Теперь машина снаружи двора.',boundary,'exit-ride',['Джон ', ' из двора на такси.'],'John left the courtyard by taxi.','выехать','выехал','«Выехал» describes leaving a space by transport.','«Выехал» — движение наружу на транспорте.'),
    ]
    result=[]
    for key,scene,en,ru,choices,answer,segments,translation,lemma,form,explanation,explanation_ru in rows:
        grammar = {'tense':'pres','person':'3per','number':'sing'} if choices is present else {'tense':'past','gender':'masc','number':'sing'}
        result.append(item('motion-'+key,'motion',scene,en,ru,segments,[choices],[answer],translation,[(explanation,explanation_ru)],
            'Check how he travels, when it happens, and whether this is a habit, an arrival or a departure.',
            'Учитывайте способ движения, время и направление. Это привычка, прибытие или отъезд?',
            (lemma,form,'VERB',grammar,{'идёт':'is walking','ходит':'walks regularly','едет':'is travelling','ездит':'travels regularly'}.get(form, translation.removeprefix('John ').rstrip('.')))))
    return result


def _placements():
    verbs = slot('verb','Position or action','Положение или действие',[('lies','лежит'),('stands','стоит'),('lay-m','положил'),('stand-m','поставил'),('lay-f','положила'),('stand-f','поставила')])
    endings = slot('noun','Location or destination','Место или направление',[('accusative','стол'),('prepositional','столе'),('instrumental','столом')])
    result=[]
    rows=[('flat-state','book-flat','The book is resting flat on the table. Describe its current position.','Книга расположена плашмя на столешнице. Опишите её положение.', ['Книга ', ' на ', '.'], ['lies','prepositional'],'The book is lying on the table.'),
          ('upright-state','book-upright','The book is upright on the table. Describe its current position.','Книга расположена вертикально на столешнице. Опишите её положение.', ['Книга ', ' на ', '.'], ['stands','prepositional'],'The book is standing on the table.')]
    for name,ru_name in [('John','Джон'),('Anna','Анна'),('Nina','Нина'),('Ivan','Иван')]:
        male=name in ('John','Ivan')
        for flat in (True,False):
            rows.append((name.lower()+('-flat' if flat else '-upright'),'book-flat' if flat else 'book-upright',
                f'{name} has just placed the book {"flat" if flat else "upright"} on the table. Describe the completed action.',
                f'{ru_name} только что переместил{"" if male else "а"} книгу на стол. Теперь книга {"плашмя" if flat else "вертикально"}. Опишите завершённое действие.',
                [ru_name+' ', ' книгу на ', '.'], [('lay-' if flat else 'stand-')+('m' if male else 'f'),'accusative'],
                f'{name} placed the book {"flat" if flat else "upright"} on the table.'))
    for key,scene,en,ru,segments,answer,translation in rows:
        state=answer[0] in ('lies','stands')
        form='столе' if state else 'стол'
        result.append(item('placement-'+key,'placement',scene,en,ru,segments,[verbs,endings],answer,translation,
            [('«Лежит» describes a horizontal position; «стоит» an upright position. «Положил/положила» and «поставил/поставила» describe placing the object.',
              '«Лежит» — горизонтальное положение; «стоит» — вертикальное. «Положил/положила» и «поставил/поставила» — действие.'),
             ('Use «на столе» for the location.' if state else 'Use «на стол» for the destination of the placing action.',
              'Место: «на столе».' if state else 'Направление действия: «на стол».')],
            'Are you describing where the book is, or someone putting it there? Then check whether it is flat or upright.',
            'Это положение книги или действие? Затем посмотрите, горизонтально или вертикально расположена книга.',
            ('стол',form,'NOUN',{'case':'loct' if state else 'accs','number':'sing'},'table')))
    return result


def _agreement():
    banks={
        'рыжий':[('masc','рыжий'),('femn','рыжая'),('neut','рыжее'),('plural','рыжие'),('object','рыжего'),('instrumental','рыжим')],
        'деревянный':[('masc','деревянный'),('femn','деревянная'),('neut','деревянное'),('plural','деревянные'),('instrumental','деревянным'),('location','деревянном')],
        'красный':[('masc','красный'),('femn','красная'),('neut','красное'),('plural','красные'),('object','красную'),('oblique','красной')],
        'жёлтый':[('masc','жёлтый'),('femn','жёлтая'),('neut','жёлтое'),('plural','жёлтые'),('instrumental','жёлтым'),('location','жёлтом')],
    }
    rows=[
        ('cat-subject','cat-on-table','рыжий','masc','masc','nomn',['Это ', ' кот.'],'This is a ginger cat.','Назовите цвет кота в этом предложении.','ginger','«Кот» is masculine nominative. Use «рыжий».','«Кот» — мужской род, именительный падеж: «рыжий».'),
        ('cat-object','cat-on-table','рыжий','object','masc','accs',['Я вижу ', ' кота.'],'I see a ginger cat.','Опишите кота, которого вы видите.','ginger','For an animate masculine object, use «рыжего кота».','Одушевлённый объект мужского рода: «рыжего кота».'),
        ('table-subject','cat-under-table','деревянный','masc','masc','nomn',['Это ', ' стол.'],'This is a wooden table.','Назовите материал стола в этом предложении.','wooden','«Стол» is masculine nominative. Use «деревянный».','«Стол» — мужской род, именительный падеж: «деревянный».'),
        ('table-under','cat-under-table','деревянный','instrumental','masc','ablt',['Барсик под ', ' столом.'],'Barsik is under the wooden table.','Опишите материал стола, под которым находится Барсик.','wooden','The adjective agrees with instrumental «столом»: «деревянным».','Согласуйте прилагательное с творительным падежом слова «столом»: «деревянным».'),
        ('table-location','cat-on-table','деревянный','location','masc','loct',['Барсик на ', ' столе.'],'Barsik is on the wooden table.','Опишите материал стола, на котором находится Барсик.','wooden','The adjective agrees with prepositional «столе»: «деревянном».','Согласуйте прилагательное со словом «столе» в предложном падеже: «деревянном».'),
        ('book-subject','book-flat','красный','femn','femn','nomn',['Это ', ' книга.'],'This is a red book.','Назовите цвет книги в этом предложении.','red','«Книга» is feminine nominative. Use «красная».','«Книга» — женский род, именительный падеж: «красная».'),
        ('book-object','book-flat','красный','object','femn','accs',['Я вижу ', ' книгу.'],'I see a red book.','Опишите цвет книги, которую вы видите.','red','The adjective agrees with feminine accusative «книгу»: «красную».','Согласуйте прилагательное со словом «книгу» в винительном падеже: «красную».'),
        ('book-about','book-flat','красный','oblique','femn','loct',['Мы говорим о ', ' книге.'],'We are talking about the red book.','Вы обсуждаете книгу на рисунке. Укажите её цвет.','red','After «о» here, use prepositional «красной книге».','После «о» здесь нужен предложный падеж: «красной книге».'),
        ('taxi-subject','taxi','жёлтый','neut','neut','nomn',['Это ', ' такси.'],'This is a yellow taxi.','Назовите цвет такси в этом предложении.','yellow','«Такси» is neuter. Use «жёлтое» even though the noun has no changing ending.','«Такси» — средний род. Существительное не изменяется, но прилагательное согласуется с ним: «жёлтое».'),
        ('taxi-travel','taxi','жёлтый','location','neut','loct',['Джон приехал на ', ' такси.'],'John arrived in a yellow taxi.','Джон уже здесь. Укажите цвет такси, на котором он добрался.','yellow','Here «на такси» takes the prepositional case: «жёлтом». The noun itself stays unchanged.','В сочетании «на такси» здесь предложный падеж: «жёлтом». Само существительное не изменяется.'),
    ]
    result=[]
    for key,scene,lemma,answer,gender,case,segments,translation,ru,meaning,explanation,explanation_ru in rows:
        choices=slot('adjective','Adjective ending','Окончание прилагательного',banks[lemma])
        result.append(item('agreement-'+key,'agreement',scene,translation+' Choose the adjective ending.',ru,
            segments,[choices],[answer],translation,[(explanation,explanation_ru)],
            'Match the adjective to the noun’s gender and its role in this sentence.',
            'Согласуйте прилагательное с существительным по роду и падежу.',
            (lemma,dict(banks[lemma])[answer],'ADJF',{'case':case,'gender':gender,'number':'sing'},meaning)))
    return result


def _roles():
    result=[]
    girls=slot('girl','Form of “girl”','Форма слова «девочка»',[('subject','девочка'),('object','девочку'),('dative','девочке')])
    boys=slot('boy','Form of “boy”','Форма слова «мальчик»',[('subject','мальчик'),('object','мальчика'),('dative','мальчику')])
    # The same two people can be a subject, an object or a recipient. Captions
    # make the intended exchange explicit; case preserves roles across order.
    for girl in (True,False):
        actor,listener=(girls,boys) if girl else (boys,girls)
        person,other=('girl','boy') if girl else ('boy','girl')
        caller_ru,listener_ru=('Девочка','мальчику') if girl else ('Мальчик','девочке')
        caller_gen,listener_nom=('девочки','Мальчик') if girl else ('мальчика','Девочка')
        calls=f'The {person} is calling the {other}.'
        rows=[('calls',[actor,listener],['subject','object'],' зовёт ','.',calls,f'{caller_ru} обращается к {listener_ru}, чтобы привлечь внимание.'),
              ('calls-reversed',[listener,actor],['object','subject'],' зовёт ','.',calls+' Keep the same roles when the word order changes.',f'{caller_ru} обращается к {listener_ru}. Сохраните роли при другом порядке слов.'),
              ('greets',[actor,listener],['subject','dative'],' говорит ',': «Привет!»',f'The {person} says “Hello!” to the {other}.',f'{caller_ru} приветствует собеседника. Приветствие адресовано {listener_ru}.'),
              ('hears',[listener,actor],['subject','object'],' слышит ','.',f'The {other} hears the {person} calling.',f'{listener_nom} слушает: голос {caller_gen} хорошо слышен.'),
              ('thanks',[actor,listener],['subject','object'],' благодарит ','.',f'The {person} is thanking the {other}.',f'{caller_ru} обращается к {listener_ru} со словом «спасибо».')]
        for key,parts,answers,verb,suffix,en,ru in rows:
            explanations=[]
            for part,answer in zip(parts,answers):
                if answer=='subject':
                    explanations.append(('This person does the action: use the nominative form.','Этот человек выполняет действие: нужен именительный падеж.'))
                elif answer=='dative':
                    explanations.append(('This is the person being spoken to: «говорит кому?» takes the dative.','Это адресат речи: «говорит кому?» требует дательного падежа.'))
                else:
                    explanations.append(('This person is the object of the verb: use the accusative form.','На этого человека направлено действие: нужен винительный падеж.'))
            target_index=next(i for i,a in enumerate(answers) if a!='subject')
            target=parts[target_index]
            answer=answers[target_index]
            form=next(c['text'] for c in target['choices'] if c['id']==target['id']+':'+answer)
            result.append(item(f'roles-{"girl" if girl else "boy"}-{key}','roles','girl-calls-boy' if girl else 'boy-calls-girl',
                en,ru,['',verb,suffix],parts,answers,
                calls if key=='calls-reversed' else f'The {other} hears the {person}.' if key=='hears' else en,explanations,
                'Identify who acts and who receives the action. Being first in the sentence does not always mean being the subject.',
                'Определите, кто действует и к кому обращено действие. Первое слово не всегда обозначает действующее лицо.',
                ('девочка' if target['id']=='girl' else 'мальчик',form,'NOUN',{'case':'datv' if answer=='dative' else 'accs','number':'sing'},'girl' if target['id']=='girl' else 'boy')))
    return result


def curriculum():
    return _locations()+_motions()+_placements()+_agreement()+_roles()


def options(value):
    from contracts.learning import fields
    fields(value,set(),{'grammar_focus','rounds'})
    focus, rounds=value.get('grammar_focus','location'), value.get('rounds',5)
    if focus not in (*FAMILIES,'mixed') or type(rounds) is not int or rounds not in (5,10):
        raise LearningError('invalid_options','Choose a grammar focus and five or ten rounds.')
    return {'grammar_focus':focus,'rounds':rounds,'word_policy':'mixed-v1'}


def build_content(seed, settings):
    rng=random.Random(seed)
    families={family:[round for round in curriculum() if round['scene_builder']['family']==family] for family in FAMILIES}
    for rounds in families.values():
        rng.shuffle(rounds)
    if settings['grammar_focus']=='mixed':
        selected=[families[FAMILIES[index%len(FAMILIES)]].pop() for index in range(settings['rounds'])]
    else:
        selected=families[settings['grammar_focus']][:settings['rounds']]
    # The snapshot travels with the session, so future editorial changes never
    # silently change an unfinished question, its answers or its reward identity.
    # Shuffling or changing the round count does not mint another daily reward
    # for repeating the same authored focus.
    lesson_version=VERSION+':'+settings['grammar_focus']
    vocabulary=list({(r['vocabulary']['lemma'],r['vocabulary']['sentence']):r['vocabulary'] for r in selected if 'vocabulary' in r}.values())
    return {'version':VERSION,'lesson_version':lesson_version,'title':GAME['title'],'options':settings,
            'source':{'kind':'grammar','lesson_id':'scene-builder','title':'Russian grammar','href':'#games/scene-builder'},
            'rounds':selected,'vocabulary_refs':vocabulary,'media_texts':[]}


def start(request_id, value, *, new_game=False, sample=False):
    from services.first_delivery import _owner
    from services.journey_games import _scope, _public, _read_row
    from services.game_access import require_access, mark_started
    settings=options({} if value is None else value)
    if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,128}',request_id):
        raise LearningError('invalid_request','Start the game again to create a new request.')
    with transaction(current_app.config['DB_PATH'],write=True) as conn:
        profile,guest=_owner(conn)
        where,params=_scope(profile,guest)
        now=timestamp()
        rows=conn.execute('SELECT * FROM journey_game_sessions WHERE '+where+' AND game_id=? ORDER BY created_at DESC,rowid DESC',(*params,GAME['id'])).fetchall()
        original=next((row for row in rows if request_id in json.loads(row['request_ids_json'])),None)
        if original:
            if json.loads(original['content_json']).get('options')!=settings:
                raise LearningError('idempotency_conflict','This start request already has a different grammar focus.',409)
            return _public(conn,original)
        active=next((row for row in rows if row['completed_at'] is None and row['superseded_at'] is None),None)
        if active and not new_game and json.loads(active['content_json'])['options']==settings:
            conn.execute('UPDATE journey_game_sessions SET request_ids_json=? WHERE id=?',(encoded([*json.loads(active['request_ids_json']),request_id]),active['id']))
            return _public(conn,active)
        if not sample:
            require_access(conn, profile, GAME['id'], now=now)
        seed,session_id=identifier(),identifier()
        content=build_content(seed,settings)
        content['sample']=sample
        if active:
            conn.execute('UPDATE journey_game_sessions SET superseded_at=? WHERE id=?',(now,active['id']))
        mark_started(conn, profile, GAME['id'], now)
        conn.execute('INSERT INTO journey_game_sessions(id,profile_id,guest_token,game_id,seed,request_ids_json,content_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)',
                     (session_id,profile,guest,GAME['id'],seed,encoded([request_id]),encoded(content),now,now))
        return _public(conn,_read_row(conn,session_id,profile,guest))


def slot_results(item, answer):
    results=[]
    for position,part in enumerate(item['scene_builder']['slots']):
        expected=item['expected_answer'][position]
        explanation,explanation_ru=item['slot_explanations'][position]
        results.append({'id':part['id'],'correct':answer[position]==expected,'expected':expected,
                        'text':next(choice['text'] for choice in part['choices'] if choice['id']==expected),
                        'explanation':explanation,'explanation_ru':explanation_ru})
    return results

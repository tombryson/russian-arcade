"""Authored motion contrasts. Level changes the task, not lexical difficulty.

Facts about mode, repetition and boundaries belong in the situation; a still
illustration cannot establish all of them. Choice banks share tense/person.
"""

LEVELS = ('A1', 'A2', 'B1')
CHOICE_COUNTS = {'A1': 2, 'A2': 4, 'B1': 6}

# key: lemma, surface form, contextual English meaning
FORMS = {
    'walk': ('идти', 'идёт', 'is walking'), 'ride': ('ехать', 'едет', 'is travelling'),
    'walk-regular': ('ходить', 'ходит', 'makes regular trips on foot'),
    'ride-regular': ('ездить', 'ездит', 'makes regular trips by transport'),
    'arrive-foot': ('прийти', 'пришёл', 'arrived on foot'),
    'arrive-ride': ('приехать', 'приехал', 'arrived by transport'),
    'leave-foot': ('уйти', 'ушёл', 'left on foot'),
    'leave-ride': ('уехать', 'уехал', 'left by transport'),
    'enter-foot': ('войти', 'вошёл', 'went inside'),
    'exit-foot': ('выйти', 'вышел', 'came outside'),
    'enter-ride': ('въехать', 'въехал', 'drove in'),
    'exit-ride': ('выехать', 'выехал', 'drove out'),
    'approach-foot': ('подойти', 'подошёл', 'walked up to'),
    'away-foot': ('отойти', 'отошёл', 'stepped away from'),
    'approach-ride': ('подъехать', 'подъехал', 'drove up to'),
    'away-ride': ('отъехать', 'отъехал', 'drove away from'),
    'pass-foot': ('пройти', 'прошёл', 'walked past'),
    'cross-foot': ('перейти', 'перешёл', 'crossed on foot'),
    'round-foot': ('обойти', 'обошёл', 'walked around'),
    'pass-ride': ('проехать', 'проехал', 'drove past'),
    'cross-ride': ('переехать', 'переехал', 'crossed by vehicle'),
    'round-ride': ('объехать', 'объехал', 'drove around'),
    'swim-across': ('переплыть', 'переплыл', 'swam across'),
    'fly-across': ('перелететь', 'перелетел', 'flew across'),
    'carry': ('нести', 'несёт', 'is carrying'),
    'carry-regular': ('носить', 'носит', 'carries regularly'),
    'lead': ('вести', 'ведёт', 'is taking someone on foot'),
    'lead-regular': ('водить', 'водит', 'takes someone on foot regularly'),
    'transport': ('везти', 'везёт', 'is transporting'),
    'transport-regular': ('возить', 'возит', 'transports regularly'),
}
PRESENT = {'walk', 'ride', 'walk-regular', 'ride-regular', 'carry', 'carry-regular',
           'lead', 'lead-regular', 'transport', 'transport-regular'}
BANKS = {
    'now': ('walk', 'ride'),
    'routine': ('walk-regular', 'ride-regular'),
    'arrival': ('arrive-foot', 'arrive-ride', 'approach-foot', 'approach-ride'),
    'departure': ('leave-foot', 'leave-ride', 'away-foot', 'away-ride'),
    'boundary': ('enter-foot', 'exit-foot', 'enter-ride', 'exit-ride'),
    'approach': ('approach-foot', 'away-foot', 'approach-ride', 'away-ride'),
    'crossing': ('cross-foot', 'round-foot', 'cross-ride', 'round-ride'),
    'route': ('pass-foot', 'cross-foot', 'round-foot', 'pass-ride', 'cross-ride', 'round-ride'),
    'crossing-b1': ('cross-foot', 'cross-ride', 'swim-across', 'fly-across', 'round-foot', 'round-ride'),
    'carrying': ('carry', 'carry-regular', 'lead', 'lead-regular', 'transport', 'transport-regular'),
}
EXPLANATIONS = {
    'walk': ('This journey is on foot: «идёт».', 'Сейчас человек движется пешком: «идёт».'),
    'ride': ('This journey uses transport: «едет».', 'Сейчас человек движется на транспорте: «едет».'),
    'walk-regular': ('These repeated journeys on foot use «ходит».', 'Регулярные походы туда и обратно: «ходит».'),
    'ride-regular': ('These repeated journeys by transport use «ездит».', 'Регулярные поездки туда и обратно: «ездит».'),
    'arrive-foot': ('He has reached his destination on foot: «пришёл».', 'Он добрался до места пешком: «пришёл».'),
    'arrive-ride': ('He has reached his destination by transport: «приехал».', 'Он добрался до места на транспорте: «приехал».'),
    'leave-foot': ('He has left the place on foot: «ушёл».', 'Он покинул это место пешком: «ушёл».'),
    'leave-ride': ('He has left the place by transport: «уехал».', 'Он покинул это место на транспорте: «уехал».'),
    'enter-foot': ('He crossed the doorway into the building: «вошёл».', 'Он пересёк порог внутрь здания: «вошёл».'),
    'exit-foot': ('He crossed the doorway to the outside: «вышел».', 'Он пересёк порог наружу: «вышел».'),
    'enter-ride': ('The vehicle crossed the entrance going in: «въехал».', 'Движение на транспорте внутрь: «въехал».'),
    'exit-ride': ('The vehicle crossed the entrance going out: «выехал».', 'Движение на транспорте наружу: «выехал».'),
    'approach-foot': ('He moved closer on foot: «подошёл».', 'Он приблизился пешком: «подошёл».'),
    'away-foot': ('He moved away on foot: «отошёл».', 'Он отдалился пешком: «отошёл».'),
    'approach-ride': ('He moved closer in a vehicle: «подъехал».', 'Он приблизился на машине: «подъехал».'),
    'away-ride': ('He moved away in a vehicle: «отъехал».', 'Он отдалился на машине: «отъехал».'),
    'pass-foot': ('He walked past without stopping: «прошёл мимо».', 'Он продолжил путь пешком, не останавливаясь: «прошёл мимо».'),
    'cross-foot': ('He went from one side to the other on foot: «перешёл».', 'Он оказался на другой стороне, двигаясь пешком: «перешёл».'),
    'round-foot': ('He went around the obstacle on foot: «обошёл».', 'Он выбрал путь пешком вокруг препятствия: «обошёл».'),
    'pass-ride': ('He went past in a vehicle without stopping: «проехал мимо».', 'Он продолжил путь на машине без остановки: «проехал мимо».'),
    'cross-ride': ('The vehicle went from one side to the other: «переехал».', 'Он оказался на другой стороне на машине: «переехал».'),
    'round-ride': ('He took a vehicle around the obstacle: «объехал».', 'Он выбрал объезд препятствия на машине: «объехал».'),
    'carry': ('The object is in their hands during this journey: «несёт».', 'Человек держит предмет в руках во время этого движения: «несёт».'),
    'carry-regular': ('This is repeated carrying in the hands: «носит».', 'Это повторяющаяся переноска предметов в руках: «носит».'),
    'lead': ('The other person or animal walks with them: «ведёт».', 'Человек или животное движется рядом пешком: «ведёт».'),
    'lead-regular': ('They regularly take someone there on foot: «водит».', 'Человек регулярно сопровождает кого-то пешком: «водит».'),
    'transport': ('The person or parcel is being moved in a vehicle: «везёт».', 'Человека или груз сейчас перевозят на транспорте: «везёт».'),
    'transport-regular': ('This is a regular transport service: «возит».', 'Это регулярная перевозка на транспорте: «возит».'),
}


def specifications():
    rows = []

    def add(key, level, bank, answers, segments, en, ru, translation, mode, stage, setting, destination, transport=None, *, banks=None, obstacle=None):
        rows.append(dict(key=key, level=level, bank=bank, answers=answers, segments=segments,
                         en=en, ru=ru, translation=translation, banks=banks, visual=dict(mode=mode, stage=stage,
                         setting=setting, destination=destination, **({'transport': transport} if transport else {}), **({'obstacle': obstacle} if obstacle else {}))))

    # A1: two meaningful alternatives. Separate mode and repetition, rather
    # than falsely rejecting an outward-leg verb after "every morning".
    add('pharmacy-walk','A1','now',['walk'],['Анна сейчас ', ' в аптеку.'],
        'Anna needs medicine. The pharmacy is on the next street; she is walking there now.',
        'Анне нужно лекарство. Аптека на соседней улице; сейчас Анна на пути туда пешком.',
        'Anna is walking to the pharmacy now.','foot','journey','shop','Аптека')
    add('work-bus','A1','now',['ride'],['Иван сейчас ', ' на работу на автобусе.'],
        'Ivan is on a bus. His workplace is on the other side of town, and he is halfway there.',
        'Иван в автобусе. Работа на другом конце города; он ещё в пути.',
        'Ivan is taking the bus to work now.','transport','journey','street','Работа','bus')
    add('station-taxi','A1','now',['ride'],['Анна сейчас ', ' на вокзал на такси.'],
        'Anna has a heavy suitcase and a train to catch. She is in a taxi on the way to the station.',
        'У Анны тяжёлый чемодан, и скоро поезд. Сейчас она в такси по дороге на вокзал.',
        'Anna is taking a taxi to the station now.','transport','journey','station','Вокзал','taxi')
    add('library-walk','A1','now',['walk'],['Иван сейчас ', ' в библиотеку.'],
        'Ivan is returning a book. He is walking along the pavement toward the nearby library.',
        'Ивану нужно вернуть книгу. Он сейчас на тротуаре по дороге в ближайшую библиотеку. Иван передвигается пешком.',
        'Ivan is walking to the library now.','foot','journey','street','Библиотека')
    add('grandparents-train','A1','now',['ride'],['Анна сейчас ', ' к бабушке на поезде.'],
        'Anna is sitting on a train. Her grandmother lives in another town; the journey is still in progress.',
        'Анна сидит в поезде. Бабушка живёт в другом городе; поезд ещё в пути.',
        'Anna is travelling to her grandmother’s by train now.','transport','journey','station','Другой город','train')
    add('park-walk','A1','now',['walk'],['Иван сейчас ', ' в парк.'],
        'The park is near Ivan’s home. He is walking there to meet a friend.',
        'Парк рядом с домом Ивана. Сейчас он пешком на пути туда, чтобы встретить друга.',
        'Ivan is walking to the park now.','foot','journey','park','Парк')
    add('work-routine','A1','routine',['ride-regular'],['Иван обычно ', ' на работу и обратно на автобусе.'],
        'Ivan’s normal routine is the bus to work and the bus home. Describe these regular journeys.',
        'Иван обычно добирается на работу и домой на автобусе. Речь о регулярных поездках.',
        'Ivan usually travels to work and back by bus.','transport','habit','street','Работа','bus')
    add('school-routine','A1','routine',['walk-regular'],['Анна обычно ', ' в школу и обратно пешком.'],
        'Anna’s school is nearby. She walks there and back on school days; this describes her routine.',
        'Школа Анны рядом. В учебные дни она добирается туда и обратно пешком; это её обычный распорядок.',
        'Anna usually walks to school and back.','foot','habit','street','Школа')
    add('library-routine','A1','routine',['walk-regular'],['Иван часто ', ' в библиотеку и обратно пешком.'],
        'Ivan often makes the short trip to the library and back on foot. Describe his habit.',
        'Иван часто бывает в библиотеке и добирается туда и обратно пешком. Это его привычка.',
        'Ivan often walks to the library and back.','foot','habit','street','Библиотека')
    add('town-routine','A1','routine',['ride-regular'],['Анна часто ', ' в соседний город и обратно на поезде.'],
        'Anna often visits relatives in the next town. Both the outward journey and the return are by train.',
        'Анна часто навещает родственников в соседнем городе. Туда и обратно она добирается на поезде.',
        'Anna often travels to the next town and back by train.','transport','habit','station','Другой город','train')
    add('pool-routine','A1','routine',['walk-regular'],['Иван обычно ', ' в бассейн и обратно пешком.'],
        'Ivan swims three times a week. The pool is nearby, and he makes both journeys on foot.',
        'Иван плавает три раза в неделю. Бассейн рядом, и в обе стороны он добирается пешком.',
        'Ivan usually walks to the swimming pool and back.','foot','habit','street','Бассейн')
    add('family-routine','A1','routine',['ride-regular'],['Анна обычно ', ' к родителям и обратно на машине.'],
        'Anna’s parents live far outside town. On her regular visits, she uses a car for both journeys.',
        'Родители Анны живут далеко за городом. Для регулярных поездок туда и обратно Анна пользуется машиной.',
        'Anna usually drives to her parents’ home and back.','transport','habit','home','Дом родителей','car')

    # A2: endpoint, boundary and relative movement are distinct choice banks.
    add('clinic-arrival','A2','arrival',['arrive-foot'],['Иван ', ' в поликлинику пешком.'],
        'Ivan walked from home to his appointment. He has reached the clinic and is waiting there.',
        'Иван добрался из дома до поликлиники пешком. Теперь он на месте и ждёт приёма.',
        'Ivan arrived at the clinic on foot.','foot','arrival','street','Поликлиника')
    add('airport-arrival','A2','arrival',['arrive-ride'],['Сергей ', ' в аэропорт на такси.'],
        'Sergei’s taxi journey is over. He is at the airport with his luggage, ready to check in.',
        'Поездка Сергея на такси закончилась. Он уже в аэропорту с багажом и готов к регистрации.',
        'Sergei arrived at the airport by taxi.','transport','arrival','airport','Аэропорт','taxi')
    add('library-departure','A2','departure',['leave-foot'],['Иван ', ' из библиотеки пешком.'],
        'Ivan has returned his books. He left the library on foot and is now several streets away.',
        'Иван вернул книги. Его уже нет в библиотеке: он пешком в нескольких улицах от неё.',
        'Ivan left the library on foot.','foot','departure','street','Библиотека')
    add('station-departure','A2','departure',['leave-ride'],['Сергей ', ' с вокзала на такси.'],
        'Sergei’s train arrived. He then took a taxi away from the station and is now on the road home.',
        'Поезд Сергея прибыл. Потом такси забрало его с вокзала; теперь он по дороге домой.',
        'Sergei left the station by taxi.','transport','departure','station','Вокзал','taxi')
    add('pharmacy-enter','A2','boundary',['enter-foot'],['Иван ', ' в аптеку.'],
        'Ivan was outside the pharmacy. He crossed the doorway on foot and is now inside.',
        'Иван был снаружи аптеки. Он пересёк порог пешком и теперь находится внутри.',
        'Ivan went into the pharmacy.','foot','enter','shop','Аптека')
    add('library-exit','A2','boundary',['exit-foot'],['Иван ', ' из библиотеки.'],
        'Ivan was inside the library. He crossed the doorway on foot and is now on the pavement outside.',
        'Иван был внутри библиотеки. Он пересёк порог пешком и теперь стоит на тротуаре снаружи.',
        'Ivan came out of the library.','foot','exit','street','Библиотека')
    add('courtyard-enter','A2','boundary',['enter-ride'],['Сергей ', ' во двор на машине.'],
        'Sergei drove through the open gate. All four wheels are now inside the courtyard.',
        'Сергей проехал через открытые ворота на машине. Теперь все четыре колеса внутри двора.',
        'Sergei drove into the courtyard.','transport','enter','courtyard','Двор','car')
    add('courtyard-exit','A2','boundary',['exit-ride'],['Сергей ', ' из двора на машине.'],
        'Sergei drove through the gate to the street. His car is now entirely outside the courtyard.',
        'Сергей проехал через ворота на машине в сторону улицы. Теперь машина полностью снаружи двора.',
        'Sergei drove out of the courtyard.','transport','exit','courtyard','Двор','car')
    add('park-approach','A2','approach',['approach-foot'],['Иван ', ' к воротам парка.'],
        'Ivan was walking along the street. He moved close to the park gate on foot and stopped beside it.',
        'Иван был на улице. Он пешком приблизился к воротам парка и остановился рядом с ними.',
        'Ivan walked up to the park gate.','foot','approach','park','Парк')
    add('station-approach','A2','approach',['approach-ride'],['Сергей ', ' к вокзалу на машине.'],
        'Sergei is collecting a friend. He drove close to the station entrance and stopped at the kerb.',
        'Сергей встречает друга. Он приблизился на машине ко входу вокзала и остановился у тротуара.',
        'Sergei drove up to the station.','transport','approach','station','Вокзал','car')
    add('gate-away','A2','approach',['away-foot'],['Иван ', ' от ворот парка.'],
        'The park gate is about to open. Ivan stepped back from it to make room.',
        'Ворота парка сейчас откроются. Иван сделал несколько шагов назад, чтобы освободить место.',
        'Ivan stepped away from the park gate.','foot','departure','park','Парк')
    add('car-away','A2','approach',['away-ride'],['Сергей ', ' от ворот на машине.'],
        'Sergei’s car was blocking the gate. He drove a few metres away to clear the entrance.',
        'Машина Сергея мешала у ворот. Он переместил её на несколько метров, освободив въезд.',
        'Sergei drove away from the gate.','transport','departure','courtyard','Ворота','car')
    add('bridge-cross','A2','crossing',['cross-foot'],['Иван ', ' реку по мосту.'],
        'Ivan was on the near riverbank. He walked across the bridge and is now on the opposite bank.',
        'Иван был на ближнем берегу. Он пешком пересёк мост и теперь на противоположном берегу.',
        'Ivan crossed the river using the bridge.','foot','cross','bridge','Другой берег')
    add('bridge-drive','A2','crossing',['cross-ride'],['Сергей ', ' реку по мосту на машине.'],
        'Sergei drove across the bridge. His car is now on the other side of the river.',
        'Сергей пересёк мост на машине. Теперь машина на другом берегу реки.',
        'Sergei drove across the river using the bridge.','transport','cross','bridge','Другой берег','car')
    add('puddle-detour','A2','crossing',['round-foot'],['Иван ', ' лужу.'],
        'A large puddle blocked Ivan’s path. He walked around its edge and kept his shoes dry.',
        'Большая лужа преградила Ивану путь. Он выбрал сухой путь по её краю, и обувь осталась сухой.',
        'Ivan walked around the puddle.','foot','detour','park','Парк',obstacle='puddle')
    add('roadworks-detour','A2','crossing',['round-ride'],['Сергей ', ' участок дорожных работ на машине.'],
        'Roadworks blocked the street. Sergei stayed in his car and used a side road around the closed section.',
        'Из-за дорожных работ улица закрыта. Сергей остался в машине и выбрал боковую дорогу вокруг закрытого участка.',
        'Sergei drove around the roadworks.','transport','detour','street','Дорожные работы','car',obstacle='roadworks')

    # B1: six relevant forms, with route sequences or an explicit transported
    # object/companion. A second blank is a second decision, not filler.
    add('parcel-hands','B1','carrying',['carry'],['Анна сейчас ', ' посылку на почту.'],
        'Anna is walking to the post office with a parcel in her hands. She is halfway there.',
        'Анна пешком по дороге на почту. Посылка у неё в руках; она ещё в пути.',
        'Anna is carrying a parcel to the post office now.','carrying','journey','street','Почта')
    add('parcel-vehicle','B1','carrying',['transport'],['Курьер сейчас ', ' посылку на склад.'],
        'A courier is driving to the warehouse. The parcel is in the back of his vehicle.',
        'Курьер сейчас за рулём по дороге на склад. Посылка лежит в кузове машины.',
        'The courier is transporting a parcel to the warehouse now.','transport','journey','street','Склад','car')
    add('child-walking','B1','carrying',['lead'],['Отец сейчас ', ' ребёнка в детский сад.'],
        'A father and child are walking to kindergarten. The child walks beside him, holding his hand.',
        'Отец и ребёнок пешком по дороге в детский сад. Ребёнок шагает рядом и держит отца за руку.',
        'The father is taking his child to kindergarten on foot now.','leading','journey','street','Детский сад')
    add('supplies-routine','B1','carrying',['carry-regular'],['Анна по работе постоянно ', ' коробки со склада в магазин и обратно.'],
        'Anna’s job includes repeated trips between the stockroom and shop, carrying boxes in her hands in both directions.',
        'Работа Анны включает постоянные перемещения между складом и магазином с коробками в руках в обе стороны.',
        'Anna regularly carries boxes between the stockroom and the shop for work.','carrying','habit','shop','Магазин')
    add('children-routine','B1','carrying',['lead-regular'],['Воспитатель регулярно ', ' детей в парк и обратно пешком.'],
        'The teacher regularly takes groups of children to the park and back. Everyone walks together.',
        'Воспитатель регулярно сопровождает группы детей в парк и обратно. Все передвигаются пешком вместе.',
        'The teacher regularly takes the children to the park and back on foot.','leading','habit','park','Парк')
    add('shuttle-routine','B1','carrying',['transport-regular'],['Водитель регулярно ', ' пассажиров между вокзалом и аэропортом.'],
        'This shuttle driver’s job is repeated passenger trips between the station and airport throughout the day.',
        'Работа этого водителя — многократные рейсы с пассажирами между вокзалом и аэропортом в течение дня.',
        'The driver regularly transports passengers between the station and the airport.','transport','habit','airport','Аэропорт','bus')
    add('pharmacy-crossing','B1','route',['pass-foot','cross-foot'],['Иван ', ' мимо аптеки, а затем ', ' дорогу по переходу.'],
        'Ivan walked past the pharmacy without stopping. At the crossing, he went to the opposite side of the road.',
        'Иван пешком миновал аптеку без остановки. У перехода он оказался на противоположной стороне дороги.',
        'Ivan walked past the pharmacy, then crossed the road at the crossing.','foot','cross','street','Аптека',banks=['route','crossing-b1'])
    add('station-bridge','B1','route',['pass-ride','cross-ride'],['Сергей ', ' мимо вокзала, а затем ', ' реку по мосту.'],
        'Sergei stayed in his car. He drove past the station without stopping, then crossed the bridge to the other riverbank.',
        'Сергей всё время был в машине. Вокзал остался позади без остановки; затем Сергей пересёк мост и оказался на другом берегу.',
        'Sergei drove past the station, then crossed the river using the bridge.','transport','cross','bridge','Другой берег','car',banks=['route','crossing-b1'])
    add('puddle-shop','B1','route',['round-foot','pass-foot'],['Иван ', ' лужу, а затем ', ' мимо магазина, не заходя внутрь.'],
        'Ivan stayed on foot. He took the dry path around a puddle, then continued past the shop without entering.',
        'Иван был пешком. Он выбрал сухой путь вокруг лужи, затем оставил магазин позади, не заходя внутрь.',
        'Ivan walked around the puddle, then walked past the shop without going in.','foot','detour','shop','Магазин',obstacle='puddle')
    add('works-station','B1','route',['round-ride','pass-ride'],['Сергей ', ' участок дорожных работ, а затем ', ' мимо вокзала.'],
        'Sergei drove a car around a closed roadworks section using side streets. He then passed the station without stopping.',
        'Сергей на машине выбрал боковые улицы вокруг дорожных работ. Потом вокзал остался позади без остановки.',
        'Sergei drove around the roadworks, then drove past the station.','transport','detour','station','Вокзал','car',obstacle='roadworks')
    add('park-parcel','B1','carrying',['lead','carry'],['Анна сейчас ', ' ребёнка в парк и ', ' его рюкзак.'],
        'Anna and her child are walking to the park. The child walks beside her; Anna holds his backpack in her free hand.',
        'Анна с ребёнком пешком по дороге в парк. Ребёнок шагает рядом; в свободной руке Анны его рюкзак.',
        'Anna is taking her child to the park on foot and carrying his backpack.','leading','journey','park','Парк')
    add('two-deliveries','B1','carrying',['carry','transport'],['Иван сейчас ', ' посылку на почту, а Сергей ', ' туда тяжёлые ящики на машине.'],
        'Ivan is walking to the post office with a parcel in his hands. At the same time, Sergei is driving there with heavy crates in his car.',
        'Иван сейчас пешком по дороге на почту с посылкой в руках. Одновременно Сергей направляется туда на машине с тяжёлыми ящиками.',
        'Ivan is carrying a parcel to the post office while Sergei transports heavy crates there by car.','carrying','journey','street','Почта')
    return rows


def questions(make_item, make_slot):
    result = []
    for spec in specifications():
        banks = [BANKS[key] for key in (spec['banks'] or [spec['bank']] * len(spec['answers']))]
        assert len(banks) == len(spec['answers'])
        assert all(len(bank) == CHOICE_COUNTS[spec['level']] for bank in banks)
        parts = [make_slot('verb' if len(spec['answers']) == 1 else f'verb-{index + 1}',
                         'Verb of motion' if len(spec['answers']) == 1 else f'Verb {index + 1}',
                         'Глагол движения' if len(spec['answers']) == 1 else f'Глагол {index + 1}',
                         [(key, FORMS[key][1]) for key in banks[index]]) for index in range(len(spec['answers']))]
        references = []
        for answer in spec['answers']:
            lemma, form, meaning = FORMS[answer]
            grammar = {'tense':'pres','person':'3per','number':'sing'} if answer in PRESENT else {'tense':'past','gender':'masc','number':'sing'}
            references.append((lemma, form, 'VERB', grammar, meaning))
        row = make_item('motion-' + spec['key'], 'motion', 'motion-route', spec['en'], spec['ru'],
                        spec['segments'], parts, spec['answers'], spec['translation'],
                        [EXPLANATIONS[key] for key in spec['answers']],
                        'Check who or what is moving, how they travel, and which part of the journey is described.',
                        'Уточните, кто или что движется, каким способом и какой этап пути описан.', references[0])
        row['scene_builder'].update(level=spec['level'], skill=spec['bank'], motion_visual=spec['visual'])
        row['vocabulary_refs'] = [dict(row['vocabulary'], lemma=lemma, form=form, pos=pos, grammar=grammar,
                                        target_meaning=meaning) for lemma,form,pos,grammar,meaning in references]
        result.append(row)
    return result

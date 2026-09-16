import {
    h,
    useState,
    useEffect,
    useRef,
} from './preact_deps.js';
import { WordModal } from './WordModal.js';
import { uiText } from './ui_text.js';

const wordCache = new Map();

export function StoryText({ words, initialVisibility }) {
    const [visibility, setVisibility] = useState(
        initialVisibility || 'revealed',
    );
    const [hiddenIndices, setHiddenIndices] = useState([]);
    const [hoveredWord, setHoveredWord] = useState(null);
    const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 });
    const [hoveredIndex, setHoveredIndex] = useState(null); // Track hovered word for color change
    const vocabCache = new Set(
        JSON.parse(localStorage.getItem('vocabCache') || '[]'),
    );
    const debounceTimeout = useRef(null);

    const toggleVisibility = (newVisibility) => {
        setVisibility(newVisibility);
        if (newVisibility === 'partially_hidden') {
            const wordIndices = words
                .map((word, idx) =>
                    word.lemma &&
                    ![
                        'в',
                        'и',
                        'с',
                        'по',
                        'на',
                        'а',
                        'но',
                        'из',
                        'к',
                        'у',
                    ].includes(word.lemma.toLowerCase())
                        ? idx
                        : null,
                )
                .filter((idx) => idx !== null);
            const numToHide = Math.floor(wordIndices.length * 0.3);
            const shuffled = wordIndices.sort(() => 0.5 - Math.random());
            setHiddenIndices(shuffled.slice(0, numToHide));
        } else if (newVisibility === 'fully_hidden') {
            const wordIndices = words
                .map((word, idx) => (word.lemma ? idx : null))
                .filter((idx) => idx !== null);
            setHiddenIndices(wordIndices);
        } else {
            setHiddenIndices([]);
        }
    };

    const handleMouseEnter = (word, index) => {
        if (debounceTimeout.current) clearTimeout(debounceTimeout.current);
        debounceTimeout.current = setTimeout(() => {
            setHoveredIndex(index); // Highlight word
        }, 100);
    };

    const handleMouseLeave = () => {
        if (debounceTimeout.current) clearTimeout(debounceTimeout.current);
        setHoveredIndex(null); // Remove highlight
    };

    const handleClick = async (word, index, event) => {
        if (word.lemma) {
            const rect = event.target.getBoundingClientRect();
            const modalWidth = 150;
            const modalHeight = 120;
            let x = rect.left + rect.width / 2 - modalWidth / 2;
            let y = rect.top - modalHeight - 10;
            x = Math.max(0, Math.min(x, window.innerWidth - modalWidth));
            y = Math.max(0, Math.min(y, window.innerHeight - modalHeight));
            let wordData;
            if (wordCache.has(word.lemma)) {
                wordData = wordCache.get(word.lemma);
            } else {
                try {
                    const response = await fetch(
                        `/word-details/${encodeURIComponent(
                            word.lemma,
                        )}?json=1`,
                    );
                    if (!response.ok)
                        throw new Error(
                            `HTTP error! status: ${response.status}`,
                    );
                    wordData = await response.json();
                    wordCache.set(word.lemma, wordData);
                } catch (error) {
                    console.error('Error fetching word details:', error);
                    wordData = {
                        translation: 'Перевод недоступен',
                        pos: 'unknown',
                        status: vocabCache.has(word.lemma)
                            ? 'Уже в списке слов'
                            : '',
                    };
                    wordCache.set(word.lemma, wordData);
                }
            }
            setHoveredWord({ ...word, ...wordData });
            setModalPosition({ x, y });
        }
    };

    const closeModal = () => {
        setHoveredWord(null);
    };

    // Handle clicks outside the modal to close it
    useEffect(() => {
        const handleOutsideClick = (event) => {
            if (hoveredWord && !event.target.closest('.tooltip')) {
                closeModal();
            }
        };
        document.addEventListener('click', handleOutsideClick);
        return () => document.removeEventListener('click', handleOutsideClick);
    }, [hoveredWord]);

    const renderedText = words.map((word, i) => {
        if (word.word === ' ' || !word.lemma) {
            return word.word;
        }
        const isHidden = hiddenIndices.includes(i);
        return h(
            'span',
            {
                key: i,
                className: `word-span ${word.added ? 'added' : ''} ${
                    isHidden
                        ? 'hidden-word'
                        : `revealed-word ${
                              hoveredIndex === i ? 'hover:text-blue-500' : ''
                          }`
                }`,
                onMouseEnter: isHidden ? null : () => handleMouseEnter(word, i),
                onMouseLeave: isHidden ? null : handleMouseLeave,
                onClick: isHidden ? null : (e) => handleClick(word, i, e),
                role: isHidden ? undefined : 'button',
                tabIndex: isHidden ? undefined : 0,
                onKeyDown: isHidden ? null : (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        handleClick(word, i, event);
                    }
                },
                style: {
                    cursor: isHidden ? 'default' : 'pointer',
                    position: 'relative',
                },
            },
            isHidden ? '____' : word.word,
        );
    });

    return h(
        'div',
        { className: 'story-text', style: { position: 'relative', zIndex: 1 } },
        visibility !== 'fully_hidden'
            ? h('div', { id: 'story-text', className: 'mb-3', lang: 'ru', style: { whiteSpace: 'pre-wrap' } }, renderedText)
            : h(
                  'p',
                  null,
                  uiText('story_hidden'),
              ),
        hoveredWord &&
            h(WordModal, {
                word: hoveredWord,
                position: modalPosition,
                onClose: closeModal,
            }),
        h(
            'button',
            {
                onClick: () => toggleVisibility('revealed'),
                'aria-pressed': visibility === 'revealed',
                className: 'btn btn-secondary me-2',
            },
            uiText('show_text'),
        ),
        h(
            'button',
            {
                onClick: () => toggleVisibility('partially_hidden'),
                'aria-pressed': visibility === 'partially_hidden',
                className: 'btn btn-secondary me-2',
            },
            uiText('hide_some_words'),
        ),
        h(
            'button',
            {
                onClick: () => toggleVisibility('fully_hidden'),
                'aria-pressed': visibility === 'fully_hidden',
                className: 'btn btn-secondary',
            },
            uiText('hide_text'),
        ),
    );
}

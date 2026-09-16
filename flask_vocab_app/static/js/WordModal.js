import { h } from './preact_deps.js';
import { uiText } from './ui_text.js';

export function WordModal({ word, position, onClose }) {
    const status = word.added || word.status === 'Already in database'
        ? uiText('word_exists')
        : word.status || 'N/A';

    return h(
        'div',
        {
            className: 'tooltip word-modal',
            style: { left: `${position.x}px`, top: `${position.y}px` },
        },
        h(
            'div',
            {
                className: 'word-modal-header',
            },
            h(
                'button',
                {
                    className: 'btn btn-sm btn-secondary',
                    onClick: onClose,
                    'aria-label': uiText('close_word_card'),
                },
                '×',
            ),
        ),
        h(
            'p',
            { className: 'word-modal-row' },
            h('strong', null, `${uiText('word')}: `),
            word.word || 'N/A',
        ),
        h(
            'p',
            { className: 'word-modal-row' },
            h('strong', null, `${uiText('lemma')}: `),
            word.lemma || 'N/A',
        ),
        h(
            'p',
            { className: 'word-modal-row' },
            h('strong', null, `${uiText('translation')}: `),
            word.translation || 'N/A',
        ),
        h(
            'p',
            { className: 'word-modal-row' },
            h('strong', null, `${uiText('part_of_speech')}: `),
            word.pos || 'unknown',
        ),
        h(
            'p',
            { className: 'word-modal-row' },
            h('strong', null, `${uiText('status')}: `),
            status,
        ),
        !word.added &&
            word.status !== 'Already in database' &&
            h(
                'button',
                {
                    className: 'btn btn-sm btn-success mt-2 btn-full',
                    onClick: async () => {
                        try {
                            const response = await fetch(
                                `/add-vocab/${encodeURIComponent(word.lemma)}`,
                                {
                                    method: 'POST',
                                },
                            );
                            const text = await response.text();
                            document.querySelector('#notification').innerHTML =
                                text;
                            const vocabCache = new Set(
                                JSON.parse(
                                    localStorage.getItem('vocabCache') || '[]',
                                ),
                            );
                            vocabCache.add(word.lemma);
                            localStorage.setItem(
                                'vocabCache',
                                JSON.stringify([...vocabCache]),
                            );
                            // Update wordCache and trigger re-render
                            const wordCache = new Map(); // Note: Assumes wordCache is managed elsewhere or re-fetched
                            wordCache.set(word.lemma, {
                                ...word,
                                status: uiText('word_exists'),
                                added: true,
                            });
                            document.dispatchEvent(
                                new CustomEvent('updateWord', {
                                    detail: {
                                        ...word,
                                        status: uiText('word_exists'),
                                        added: true,
                                    },
                                }),
                            );
                        } catch (error) {
                            console.error('Error adding vocab:', error);
                            document.querySelector('#notification').innerHTML =
                                `<div class="alert alert-danger">${uiText('error_add_word')}</div>`;
                        }
                    },
                },
                uiText('add_to_list'),
            ),
    );
}

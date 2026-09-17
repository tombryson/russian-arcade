import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/preact';

vi.mock('../../static/js/preact_deps.js', async () => ({
  ...await import('preact'), ...await import('preact/hooks'),
}));
vi.mock('../../static/js/WordModal.js', () => ({ WordModal: () => null }));
import { StoryText } from '../../static/js/StoryText.js';
import { readFileSync } from 'node:fs';
const shellSource = readFileSync('../static/js/app_shell.js', 'utf8');

const words = [
  { word: 'Привет', lemma: 'привет' }, { word: ', ', lemma: null },
  { word: 'кот', lemma: 'кот' }, { word: '!\n\n', lemma: null },
  { word: 'Как', lemma: 'как' }, { word: ' ', lemma: null }, { word: 'дела', lemma: 'дело' },
];
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); document.documentElement.lang = 'en'; });

describe('legacy reading text', () => {
  it('retains text spacing and provides keyboard word lookup with English controls', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ translation: 'cat' }) });
    vi.stubGlobal('fetch', fetch);
    render(<StoryText words={words} initialVisibility="revealed" />);
    expect(document.getElementById('story-text').textContent).toBe('Привет, кот!\n\nКак дела');
    expect(screen.getByRole('button', { name: 'Show text' }).getAttribute('aria-pressed')).toBe('true');
    fireEvent.keyDown(screen.getByRole('button', { name: 'кот' }), { key: 'Enter' });
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/word-details/%D0%BA%D0%BE%D1%82?json=1'));
    fireEvent.click(screen.getByRole('button', { name: 'Hide text' }));
    expect(screen.queryByRole('button', { name: 'кот' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Show text' }));
    expect(document.getElementById('story-text').textContent).toBe('Привет, кот!\n\nКак дела');
  });

  it('matches the chosen Russian interface language', () => {
    document.documentElement.lang = 'ru';
    render(<StoryText words={words} initialVisibility="revealed" />);
    expect(screen.getByRole('button', { name: 'Показать текст' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Show text' })).toBeNull();
  });
});

describe('reading draft guard', () => {
  beforeAll(() => {
    // Page observation is unrelated to these request-event tests. Avoid keeping
    // its document listener alive after jsdom tears down the test environment.
    vi.stubGlobal('MutationObserver', class { observe() {} disconnect() {} });
    window.eval(shellSource);
  });

  function workspace() {
    document.body.innerHTML = `<main id="mainContent" data-page="test"><div class="reading-workspace" data-leave-message="Discard changes?">
      <details id="saved-stories"><summary>Saved stories</summary></details>
      <div id="reading-action-feedback"></div>
      <div id="comprehension-content"><form id="question-form"><textarea id="draft"></textarea></form></div>
      <button id="save-story" hx-post="/comprehension/save"></button></div></main>`;
    fireEvent.input(document.getElementById('draft'), { target: { value: 'Мой ответ.' } });
    return document.querySelector('.reading-workspace');
  }

  it('allows the library to open without discarding answers, and can cancel switching stories', () => {
    const root = workspace();
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    document.getElementById('saved-stories').open = true;
    expect(document.getElementById('draft').value).toBe('Мой ответ.');
    const request = new CustomEvent('htmx:beforeRequest', { bubbles: true, cancelable: true,
      detail: { target: document.getElementById('mainContent'), elt: document.createElement('a') } });
    document.body.dispatchEvent(request);
    expect(request.defaultPrevented).toBe(true);
    expect(confirm).toHaveBeenCalledWith('Discard changes?');
    expect(root.dataset.dirty).toBe('true');
  });

  it('keeps later edits dirty when an earlier save completes', () => {
    const root = workspace();
    const save = document.getElementById('save-story');
    const detail = { elt: save, target: document.createElement('div') };
    document.body.dispatchEvent(new CustomEvent('htmx:beforeRequest', { detail }));
    fireEvent.input(document.getElementById('draft'), { target: { value: 'Ещё один ответ.' } });
    document.body.dispatchEvent(new CustomEvent('htmx:afterRequest', { detail: { ...detail, successful: true } }));
    expect(root.dataset.dirty).toBe('true');
    document.body.dispatchEvent(new CustomEvent('htmx:beforeRequest', { detail }));
    document.body.dispatchEvent(new CustomEvent('htmx:afterRequest', { detail: { ...detail, successful: true } }));
    expect(root.dataset.dirty).toBe('false');
  });

  it('shows a failed request beside the activity without replacing the draft', () => {
    const root = workspace();
    const detail = { target: document.getElementById('comprehension-content'), xhr: { status: 503 }, shouldSwap: false };
    document.body.dispatchEvent(new CustomEvent('htmx:beforeSwap', { detail }));
    expect(detail.target).toBe(document.getElementById('reading-action-feedback'));
    expect(detail.shouldSwap).toBe(true);
    expect(document.getElementById('draft').value).toBe('Мой ответ.');
    expect(root.dataset.dirty).toBe('true');
  });

  it('retains the draft when HTMX saves a page for Back navigation', () => {
    workspace();
    document.body.dispatchEvent(new CustomEvent('htmx:beforeHistorySave'));
    const cached = document.getElementById('question-form').cloneNode(true);
    expect(cached.querySelector('textarea').textContent).toBe('Мой ответ.');
  });

  function mobileSidebar() {
    document.body.insertAdjacentHTML('afterbegin', `<nav id="sidebar">
      <button data-bs-target="#sidebarNav" aria-expanded="true">Menu</button>
      <div id="sidebarNav" class="collapse show"><a class="sidebar-link" href="/writing" hx-boost="true">Writing</a></div>
    </nav>`);
    vi.stubGlobal('innerWidth', 390);
    const menu = document.getElementById('sidebarNav');
    const hide = vi.fn(() => menu.classList.remove('show'));
    const getOrCreateInstance = vi.fn(() => ({ hide }));
    vi.stubGlobal('bootstrap', { Collapse: { getOrCreateInstance } });
    return { menu, link: menu.querySelector('a'), hide, getOrCreateInstance };
  }

  it('closes the mobile menu only after a successful boosted activity swap', () => {
    workspace().dataset.dirty = 'false';
    const { menu, link, hide, getOrCreateInstance } = mobileSidebar();
    const main = document.getElementById('mainContent');
    document.body.dispatchEvent(new CustomEvent('htmx:beforeRequest', { detail: { target: main, elt: link } }));
    expect(hide).not.toHaveBeenCalled();
    document.body.dispatchEvent(new CustomEvent('htmx:afterSettle', {
      detail: { target: main, elt: main, requestConfig: { elt: link }, xhr: { status: 200 } },
    }));
    expect(getOrCreateInstance).toHaveBeenCalledWith(menu, { toggle: false });
    expect(hide).toHaveBeenCalledOnce();
    expect(menu.classList.contains('show')).toBe(false);
  });

  it('keeps the mobile menu open when navigation is cancelled to preserve a draft', () => {
    workspace();
    const { menu, link, hide } = mobileSidebar();
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    const request = new CustomEvent('htmx:beforeRequest', { cancelable: true,
      detail: { target: document.getElementById('mainContent'), elt: link } });
    document.body.dispatchEvent(request);
    expect(request.defaultPrevented).toBe(true);
    expect(menu.classList.contains('show')).toBe(true);
    expect(hide).not.toHaveBeenCalled();
    expect(document.getElementById('draft').value).toBe('Мой ответ.');
  });

  it('does not close navigation for failed swaps, unrelated updates or desktop views', () => {
    workspace().dataset.dirty = 'false';
    const { link, hide } = mobileSidebar();
    const main = document.getElementById('mainContent');
    const settle = (source, status = 200) => document.body.dispatchEvent(new CustomEvent('htmx:afterSettle', {
      detail: { target: main, requestConfig: { elt: source }, xhr: { status } },
    }));
    settle(link, 503);
    settle(document.getElementById('save-story'));
    vi.stubGlobal('innerWidth', 1200);
    settle(link);
    expect(hide).not.toHaveBeenCalled();
  });
});

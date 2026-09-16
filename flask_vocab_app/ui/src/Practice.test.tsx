import { afterEach, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/preact';
import { Practice } from './Practice';

const initial = { id: 's1', profile_id: 'p1', title: 'Food words', revision: 0, status: 'active', completed_items: 0, total_items: 1, attempts: [], item: { id: 'i1', prompt: 'Which word means apple?', choices: [{ id: 'apple', text: 'яблоко' }, { id: 'house', text: 'дом' }], has_hint: true } };
const complete = { ...initial, revision: 1, status: 'completed', completed_items: 1, item: null, attempts: [{ id: 'answer1', feedback: { outcome: 'incorrect', answer: 'яблоко means apple.', assisted: false } }] };
const response = (value: unknown, ok = true) => Promise.resolve({ ok, json: async () => value });
afterEach(() => vi.unstubAllGlobals());

it('retries an uncertain save with the identical command and keeps the correction after remount', async () => {
  let writes = 0;
  let saved = false;
  const fetch = vi.fn((_url: string, options?: RequestInit) => {
    if (options?.method === 'POST') {
      saved = true;
      if (++writes === 1) return Promise.reject(new TypeError('Network response lost'));
      return response(complete);
    }
    return response(saved ? complete : initial);
  });
  vi.stubGlobal('fetch', fetch);
  const view = render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  fireEvent.click(await screen.findByRole('button', { name: 'дом' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Try saving again' }));
  await screen.findByRole('heading', { name: 'Let’s look at the answer.' });
  const commands = fetch.mock.calls.filter(([, options]) => options?.method === 'POST');
  expect(commands[0][1]?.body).toBe(commands[1][1]?.body);
  expect(screen.getByText('яблоко means apple.')).toBeTruthy();
  view.unmount();
  render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  expect(await screen.findByRole('heading', { name: 'Let’s look at the answer.' })).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: /Finish practice/ }));
  expect(screen.getByRole('heading', { name: 'You answered 1 question.' })).toBeTruthy();
});

it('records help before answering and preserves the updated revision', async () => {
  const fetch = vi.fn((url: string) => response(url.endsWith('/help') ? { ...initial, revision: 1, item: { ...initial.item, hint: 'Яблоко means apple.' } } : url.endsWith('/attempts') ? { ...complete, revision: 2, attempts: [{ id: 'answer1', feedback: { outcome: 'correct', answer: 'яблоко', assisted: true } }] } : initial));
  vi.stubGlobal('fetch', fetch);
  render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  fireEvent.click(await screen.findByRole('button', { name: 'Show a hint' }));
  await screen.findByText('Яблоко means apple.');
  fireEvent.click(screen.getByRole('button', { name: 'яблоко' }));
  expect(await screen.findByText('You used a hint for this question.')).toBeTruthy();
});

it('uses the latest server revision after another tab answers instead of submitting again', async () => {
  vi.stubGlobal('fetch', vi.fn((_url: string, options?: RequestInit) => options?.method === 'POST'
    ? response({ error: { code: 'stale_revision', message: 'Changed', current_session: complete } }, false) : response(initial)));
  render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  fireEvent.click(await screen.findByRole('button', { name: 'дом' }));
  expect(await screen.findByText(/Practice changed in another tab/)).toBeTruthy();
  expect(screen.queryByRole('button', { name: 'Try saving again' })).toBeNull();
  expect(screen.getByRole('heading', { name: 'Let’s look at the answer.' })).toBeTruthy();
});

it('clears the task when household access expires', async () => {
  vi.stubGlobal('fetch', vi.fn((_url: string, options?: RequestInit) => options?.method === 'POST'
    ? response({ error: { code: 'locked', message: 'Ask a grown-up to unlock this household.' } }, false) : response(initial)));
  render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  fireEvent.click(await screen.findByRole('button', { name: 'дом' }));
  expect(await screen.findByText('Ask a grown-up to unlock this household.')).toBeTruthy();
  expect(screen.queryByRole('button', { name: 'яблоко' })).toBeNull();
});

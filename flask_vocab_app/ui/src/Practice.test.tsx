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

it('keeps the curriculum return route and the saved explanation after reloading a result', async () => {
  const origin = { href: '/curriculum/units/location-destination-v1', title: 'Where and where to' };
  const finished = { ...complete, origin, attempts: [{ id: 'answer1', prompt: 'Нина ждёт тебя …', feedback: {
    outcome: 'incorrect', answer: 'На почте.', assisted: false,
    explanation: 'На почте tells us where Nina is waiting.',
  } }] };
  vi.stubGlobal('fetch', vi.fn(() => response(finished)));
  const onFinish = vi.fn();
  render(<Practice sessionId="s1" profileId="p1" onFinish={onFinish} />);
  expect(await screen.findByText('На почте tells us where Nina is waiting.')).toBeTruthy();
  expect(screen.getByRole('link', { name: 'Where and where to' }).getAttribute('href')).toBe(origin.href);
  expect(screen.getByText('Нина ждёт тебя …')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: /Finish practice/ }));
  expect(screen.getByRole('link', { name: /Continue learning/ }).getAttribute('href')).toBe(origin.href);
  expect(onFinish).not.toHaveBeenCalled();
});

it('clears an uncertain command when opening a different learner and session', async () => {
  const second = { ...initial, id: 's2', profile_id: 'p2', item: {
    ...initial.item, prompt: 'Where is the park?', choices: [{ id: 'park', text: 'парк' }],
  } };
  const fetch = vi.fn((url: string, options?: RequestInit) => options?.method === 'POST'
    ? Promise.reject(new TypeError('Network response lost'))
    : response(url.endsWith('/s2') ? second : initial));
  vi.stubGlobal('fetch', fetch);
  const view = render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  fireEvent.click(await screen.findByRole('button', { name: 'дом' }));
  await screen.findByRole('button', { name: 'Try saving again' });
  view.rerender(<Practice sessionId="s2" profileId="p2" onFinish={() => {}} />);
  const choice = await screen.findByRole('button', { name: 'парк' });
  expect((choice as HTMLButtonElement).disabled).toBe(false);
  expect(screen.queryByText('Save not confirmed')).toBeNull();
});

it('saves exact typed text, retries the same command and restores the response on reload', async () => {
  const origin = {href: '/curriculum/units/location-destination-v1', title: 'Where and where to'};
  const forms = {...initial, origin, total_items: 3, item: {id: 'form1', type: 'controlled_text', prompt: 'Барсик идёт в ___. (школа)', has_hint: true}};
  const typed = '  В ШКОЛУ!  ';
  const checked = {...forms, revision: 1, completed_items: 1, item: {...forms.item, id: 'form2'}, attempts: [{id: 'answer1', feedback: {
    outcome: 'correct', answer: 'школу', response_text: typed, assisted: false, explanation: 'His destination uses школу.',
  }}]};
  let writes = 0;
  let saved = false;
  const fetch = vi.fn((_url: string, options?: RequestInit) => {
    if(options?.method === 'POST') {saved = true; return ++writes === 1 ? Promise.reject(new TypeError('Response lost')) : response(checked);}
    return response(saved ? checked : forms);
  });
  vi.stubGlobal('fetch', fetch);
  const view = render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  const field = await screen.findByRole('textbox', {name: 'Your answer in Russian'});
  expect(screen.queryByText('Choose one answer.')).toBeNull();
  fireEvent.input(field, {target: {value: typed}});
  fireEvent.click(screen.getByRole('button', {name: 'Check answer'}));
  fireEvent.click(await screen.findByRole('button', {name: 'Try saving again'}));
  await screen.findByRole('heading', {name: 'That’s right.'});
  const commands = fetch.mock.calls.filter(([,options]) => options?.method === 'POST');
  expect(commands[0][1]?.body).toBe(commands[1][1]?.body);
  expect(JSON.parse(String(commands[0][1]?.body)).answer).toEqual({text: typed});
  expect(screen.getByText('1 of 3')).toBeTruthy();
  expect(screen.getByText('В ШКОЛУ!').textContent).toBe(typed);
  view.unmount();
  render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  expect(await screen.findByText('His destination uses школу.')).toBeTruthy();
  expect(screen.getByText('1 of 3')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', {name: /Next question/}));
  expect(screen.getByText('2 of 3')).toBeTruthy();
  expect((screen.getByRole('textbox') as HTMLInputElement).value).toBe('');
});

it('retains a typed draft while requesting a hint and displays a saved incorrect form', async () => {
  const forms = {...initial, item: {id: 'form1', type: 'controlled_text', prompt: 'Нина ждёт на ___. (почта)', has_hint: true}};
  const checked = {...complete, attempts: [{id: 'answer1', feedback: {outcome: 'incorrect', answer: 'почте', response_text: 'почта', assisted: true}}]};
  const fetch = vi.fn((url: string) => response(url.endsWith('/help') ? {...forms, revision: 1, item: {...forms.item, hint: 'Use the location ending -е.'}} : url.endsWith('/attempts') ? checked : forms));
  vi.stubGlobal('fetch', fetch);
  render(<Practice sessionId="s1" profileId="p1" onFinish={() => {}} />);
  fireEvent.input(await screen.findByRole('textbox'), {target: {value: 'почта'}});
  fireEvent.click(screen.getByRole('button', {name: 'Show a hint'}));
  await screen.findByText('Use the location ending -е.');
  expect((screen.getByRole('textbox') as HTMLInputElement).value).toBe('почта');
  fireEvent.click(screen.getByRole('button', {name: 'Check answer'}));
  await screen.findByText('You used a hint for this question.');
  expect(screen.getByText('почта')).toBeTruthy();
  expect(screen.getByText('почте')).toBeTruthy();
});

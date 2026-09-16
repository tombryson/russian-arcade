import { expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const source = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), '../../static/js/household_security.js'), 'utf8');

it('adds CSRF to legacy requests and forms without sending it to another origin', async () => {
  const meta = document.createElement('meta');
  meta.name = 'csrf-token';
  meta.content = 'fixture-token';
  document.head.append(meta);
  const originalFetch = window.fetch;
  const transport = vi.fn<typeof window.fetch>(async () => new Response('{}'));
  window.fetch = transport;
  try {
    // Execute the actual classic script, as the legacy document does.
    Function(source)();
    await window.fetch('/sync', { method: 'POST', body: 'fixture' });
    const init = transport.mock.calls[0][1] as RequestInit;
    expect(new Headers(init.headers).get('X-CSRF-Token')).toBe('fixture-token');
    expect(init.body).toBe('fixture');
    await window.fetch('https://external.invalid/upload', { method: 'POST', body: 'fixture' });
    expect(new Headers((transport.mock.calls[1][1] as RequestInit).headers).has('X-CSRF-Token')).toBe(false);
    const request = new Request(`${window.location.origin}/writing/save`, { method: 'POST', headers: { 'X-Existing': 'kept' }, body: 'answer' });
    await window.fetch(request);
    expect(new Headers((transport.mock.calls[2][1] as RequestInit).headers).get('X-Existing')).toBe('kept');
    const form = document.createElement('form');
    form.action = '/ui-language';
    document.body.append(form);
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    expect(new FormData(form).get('csrf_token')).toBe('fixture-token');
    form.remove();
    const detail = { path: '/sync_vocab', headers: {} as Record<string, string> };
    document.dispatchEvent(new CustomEvent('htmx:configRequest', { detail }));
    expect(detail.headers['X-CSRF-Token']).toBe('fixture-token');
  } finally {
    window.fetch = originalFetch;
    meta.remove();
  }
});

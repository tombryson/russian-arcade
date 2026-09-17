import { expect, it } from 'vitest';
import { render } from 'preact';
import { screen, within } from '@testing-library/preact';

it('replaces the server loading fallback when the application mounts', async () => {
  const root = document.createElement('div');
  root.id = 'word-post';
  root.dataset.view = 'app';
  root.innerHTML = '<section><h1>Opening your activities…</h1><a href="/">Existing workspace</a></section>';
  document.body.append(root);
  try {
    await import('./main');
    expect(screen.queryByRole('heading', { name: 'Opening your activities…' })).toBeNull();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(within(screen.getByRole('main')).getByRole('link', { name: /^Read a story/ })).toBeTruthy();
  } finally {
    render(null, root);
    root.remove();
  }
});

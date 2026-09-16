import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, within } from '@testing-library/preact';
import { App } from './App';
import type { ActivityNavigation } from './ActivitySidebar';

const navigation: ActivityNavigation = {
  title: 'Activities & tools', more: 'More tools',
  activities: [
    {page:'native_flashcards', href:'/post/#flashcards', label:'Flashcards', boost:false},
    {page:'writing', href:'/writing', label:'Writing', boost:true},
  ],
  tools: [{page:'flashcards', href:'/', label:'Anki card tools', boost:true}],
};
async function navigate(hash: string) {
  await act(() => {
    window.history.replaceState(null, '', `/post/#${hash}`);
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  });
}
afterEach(() => vi.unstubAllGlobals());

describe('Flashcard activity navigation', () => {
  it('keeps the menu through collection, generator and review routes, including loading or error states', async () => {
    vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ok:false, json:async () => ({error:{message:'Temporarily offline'}})}));
    await navigate('flashcards?word_id=4');
    render(<App navigation={navigation} />);
    const menu = screen.getByRole('navigation', {name:'Activities & tools'});
    for (const hash of ['flashcards', 'generate?word_id=4', 'generate/batch-1', 'review/session-1']) {
      await navigate(hash);
      expect(screen.getByRole('navigation', {name:'Activities & tools'})).toBe(menu);
      expect(within(menu).getByRole('link', {name:'Flashcards'}).getAttribute('aria-current')).toBe('page');
      expect(within(menu).getByRole('link', {name:'Writing'}).getAttribute('href')).toBe('/writing');
    }
    await navigate('home');
    expect(screen.queryByRole('navigation', {name:'Activities & tools'})).toBeNull();
    expect(screen.getByText('Hello! I’m Barsik.')).toBeTruthy();
  });

  it('lets the compact menu expand and keeps Anki inside the optional tools disclosure', async () => {
    vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ok:false, json:async () => ({error:{message:'Offline'}})}));
    await navigate('flashcards');
    render(<App navigation={navigation} />);
    const toggle = screen.getByRole('button', {name:'Activities & tools'});
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    fireEvent.click(toggle);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    const menu = screen.getByRole('navigation', {name:'Activities & tools'});
    const tools = within(menu).getByText('More tools').closest('details')!;
    expect(tools.open).toBe(false);
    expect(tools.querySelector('a')?.getAttribute('href')).toBe('/');
    fireEvent.click(within(menu).getByRole('link', {name:'Flashcards'}));
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
  });
});

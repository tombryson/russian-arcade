import { useState } from 'preact/hooks';

type ActivityLink = { page: string; href: string; label: string; boost: boolean };
export type ActivityNavigation = { title: string; more: string; activities: ActivityLink[]; tools: ActivityLink[] };

export function ActivitySidebar({ navigation }: { navigation: ActivityNavigation }) {
  const [expanded, setExpanded] = useState(false);
  return <aside class="activity-sidebar">
    <div class="activity-sidebar-title">{navigation.title}</div>
    <button class="activity-menu-toggle" type="button" aria-expanded={expanded} aria-controls="activity-navigation" onClick={() => setExpanded(value => !value)}>
      {navigation.title}<span aria-hidden="true">{expanded ? '−' : '+'}</span>
    </button>
    <nav id="activity-navigation" class="activity-navigation" data-expanded={expanded} aria-label={navigation.title}>
      <div class="activity-sidebar-links">{navigation.activities.map(item => <a key={item.page} href={item.href} aria-current={item.page === 'native_flashcards' ? 'page' : undefined} onClick={() => setExpanded(false)}>{item.label}</a>)}</div>
      <details class="activity-sidebar-more">
        <summary>{navigation.more}</summary>
        {navigation.tools.map(item => <a key={item.page} href={item.href}>{item.label}</a>)}
      </details>
    </nav>
  </aside>;
}

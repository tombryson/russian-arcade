import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/preact';
import { UserSessionLink, type UserProfile } from './UserSessionLink';

describe('User profile link', () => {
  it.each([undefined, '   '])('keeps the profile picker usable when a response has no display name: %s', displayName => {
    const profile={id:'tom',display_name:displayName} as UserProfile;
    render(<UserSessionLink profile={profile} />);
    const link=screen.getByRole('link',{name:'Your profile'});
    expect(link.getAttribute('href')).toBe('/post/profiles');
    expect(link.getAttribute('data-profile-id')).toBe('tom');
    expect(link.textContent).toBe('●');
  });
});

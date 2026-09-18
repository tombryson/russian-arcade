import type { Language } from './review-types';
import '../../static/css/user_sessions.css';

export type UserProfile={id:string;display_name:string;avatar?:string;study_timezone?:string};
export type AccountMode='local'|'preview'|'hosted';

export function UserSessionLink({profile,language='en',household=false,accountMode='local',signInAvailable=false,sessionScope}:{profile:UserProfile|null;language?:Language;household?:boolean;accountMode?:AccountMode;signInAvailable?:boolean;sessionScope?:string}) {
  const name=typeof profile?.display_name==='string' ? profile.display_name.trim() : '';
  const preview=accountMode==='preview';
  const accountLabel=language==='ru' ? 'Аккаунт' : 'Account';
  const entryLabel=preview && signInAvailable ? (language==='ru' ? 'Войти' : 'Sign in') : accountLabel;
  const label=preview ? entryLabel
    : accountMode==='hosted' ? (name ? `${accountLabel}: ${name}` : accountLabel)
    : household ? (language==='ru' ? 'Профили семьи' : 'Household profiles')
    : profile ? (name ? (language==='ru' ? `Профиль: ${name}` : `Profile: ${name}`) : (language==='ru' ? 'Ваш профиль' : 'Your profile'))
    : (language==='ru' ? 'Выбрать профиль' : 'Choose a profile');
  return <a class={`user-session-link${preview ? ' user-session-account-entry' : ''}`} href={accountMode!=='local' ? '/trial/account' : household ? '/post/household' : '/post/profiles'} aria-label={label} title={label}
    {...(accountMode!=='local' || !household ? {'data-user-session':'','data-profile-id':profile?.id ?? '','data-session-scope':sessionScope} : {})}>
    {preview ? entryLabel : profile ? <span class="user-session-initial" aria-hidden="true">{Array.from(name)[0]?.toLocaleUpperCase(language) ?? '●'}</span>
      : <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="12" cy="8" r="3.5"/><path d="M4.5 21v-2a7.5 7.5 0 0 1 15 0v2"/></svg>}
  </a>;
}

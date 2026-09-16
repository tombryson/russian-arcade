import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, bindUserSession, endOnLeave, upload } from './learning-api';

afterEach(()=>{
  bindUserSession(undefined,'');
  vi.unstubAllGlobals();
});

describe('Page identity binding',()=>{
  it('keeps every request bound to its original profile after a late response refreshes CSRF',async()=>{
    bindUserSession('profile-a','old-token');
    const fetch=vi.fn((_url:string,_options?:RequestInit)=>Promise.resolve({ok:true,json:async()=>({
      profile_id:'profile-b',profile:{id:'profile-b',display_name:'Other'},csrf_token:'new-token',
    })}));
    vi.stubGlobal('fetch',fetch);

    await api('/api/v1/progression');
    await api('/api/v1/progression/preferences',{level:'A2'});
    await upload('/api/v1/conversations/one/turns',new FormData());
    endOnLeave('/api/v1/live-conversations/one/end');

    expect(fetch).toHaveBeenCalledTimes(4);
    for (const [, options] of fetch.mock.calls) {
      expect(options?.headers).toMatchObject({'X-Profile-ID':'profile-a'});
    }
    for (const [, options] of fetch.mock.calls.slice(1)) {
      expect(options?.headers).toMatchObject({'X-CSRF-Token':'new-token'});
    }
    expect(fetch.mock.calls[3][1]).toMatchObject({keepalive:true,method:'POST'});
  });
});

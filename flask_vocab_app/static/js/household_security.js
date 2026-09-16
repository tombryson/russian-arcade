/* Temporary CSRF adapter for the legacy forms, HTMX and fetch clients. */
(() => {
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    const profile = document.querySelector('meta[name="learning-profile"]')?.content;
    if (!token) return;
    const local = value => new URL(value, window.location.href).origin === window.location.origin;
    const originalFetch = window.fetch.bind(window);
    window.fetch = (input, init = {}) => {
        const url = input instanceof Request ? input.url : String(input);
        if (!local(url)) return originalFetch(input, init);
        const headers = new Headers(init.headers ?? (input instanceof Request ? input.headers : undefined));
        headers.set('X-CSRF-Token', token);
        if (profile) headers.set('X-Profile-ID', profile);
        return originalFetch(input, { ...init, headers });
    };
    document.addEventListener('htmx:configRequest', event => {
        if (local(event.detail.path)) {
            event.detail.headers['X-CSRF-Token'] = token;
            if (profile) event.detail.headers['X-Profile-ID'] = profile;
        }
    });
    document.addEventListener('submit', event => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || !local(form.action)) return;
        let hidden = form.querySelector('input[name="csrf_token"]');
        if (!hidden) {
            hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'csrf_token';
            form.append(hidden);
        }
        hidden.value = token;
    }, true);
    document.addEventListener('formdata', event => {
        if (event.target instanceof HTMLFormElement && local(event.target.action)) event.formData.set('csrf_token', token);
    }, true);
})();

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// Add the CSRF token to every same-origin unsafe fetch request.
const originalFetch = window.fetch.bind(window);
window.fetch = function(resource, options = {}) {
    const method = String(options.method || 'GET').toUpperCase();
    const target = typeof resource === 'string' ? new URL(resource, window.location.href) : new URL(resource.url, window.location.href);
    if (target.origin === window.location.origin && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
        const headers = new Headers(options.headers || {});
        headers.set('X-CSRFToken', getCsrfToken());
        options.headers = headers;
    }
    return originalFetch(resource, options);
};

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-account-menu]').forEach((menu) => {
        const toggle = menu.querySelector('[data-account-menu-toggle]');
        const panel = menu.querySelector('[data-account-menu-panel]');
        if (!toggle || !panel) return;

        const closeMenu = ({ restoreFocus = false } = {}) => {
            panel.hidden = true;
            toggle.setAttribute('aria-expanded', 'false');
            if (restoreFocus) toggle.focus();
        };

        const openMenu = () => {
            panel.hidden = false;
            toggle.setAttribute('aria-expanded', 'true');
        };

        closeMenu();
        toggle.addEventListener('click', (event) => {
            event.stopPropagation();
            if (panel.hidden) openMenu();
            else closeMenu();
        });
        menu.addEventListener('click', (event) => event.stopPropagation());
        document.addEventListener('click', () => closeMenu());
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && !panel.hidden) {
                closeMenu({ restoreFocus: true });
            }
        });
    });

    const token = getCsrfToken();
    document.querySelectorAll('form').forEach(form => {
        const method = String(form.getAttribute('method') || 'GET').toUpperCase();
        if (!['GET', 'HEAD'].includes(method) && !form.querySelector('input[name="csrf_token"]')) {
            const field = document.createElement('input');
            field.type = 'hidden';
            field.name = 'csrf_token';
            field.value = token;
            form.prepend(field);
        }
    });

    document.querySelectorAll('.flash-alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

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

function setupDisclosure(root, toggleSelector, panelSelector) {
    const toggle = root.querySelector(toggleSelector);
    const panel = root.querySelector(panelSelector);
    if (!toggle || !panel) return null;

    const close = ({ restoreFocus = false } = {}) => {
        panel.hidden = true;
        toggle.setAttribute('aria-expanded', 'false');
        if (restoreFocus) toggle.focus();
    };
    const open = () => {
        panel.hidden = false;
        toggle.setAttribute('aria-expanded', 'true');
    };

    close();
    toggle.addEventListener('click', (event) => {
        event.stopPropagation();
        if (panel.hidden) open();
        else close();
    });
    root.addEventListener('click', (event) => event.stopPropagation());
    document.addEventListener('click', () => close());
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !panel.hidden) close({ restoreFocus: true });
    });
    return { close, open, panel, toggle };
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-dismiss-parent]').forEach((button) => {
        button.addEventListener('click', () => button.parentElement?.remove());
    });
    document.querySelectorAll('[data-copy-target]').forEach((button) => {
        button.addEventListener('click', async () => {
            const source = document.getElementById(button.dataset.copyTarget);
            if (!source) return;
            await navigator.clipboard.writeText(source.textContent || '');
            button.textContent = 'Copiado';
        });
    });
    document.querySelectorAll('[data-print]').forEach((button) => button.addEventListener('click', () => window.print()));
    document.querySelectorAll('[data-confirm-submit]').forEach((form) => {
        form.addEventListener('submit', async (event) => {
            if (form.dataset.confirmed === 'true') return;
            event.preventDefault();
            const result = await confirmarAccion({ titulo: 'Confirmar eliminación', mensaje: form.dataset.confirmSubmit, textoConfirmar: 'Eliminar' });
            if (result.isConfirmed) {
                form.dataset.confirmed = 'true';
                form.requestSubmit();
            }
        });
    });
    const sidebar = document.querySelector('[data-sidebar]');
    const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
    const sidebarClose = document.querySelector('[data-sidebar-close]');
    const sidebarOverlay = document.querySelector('[data-sidebar-overlay]');

    const closeSidebar = ({ restoreFocus = false } = {}) => {
        if (!sidebar || !sidebarToggle || !sidebarOverlay) return;
        sidebar.classList.remove('is-open');
        sidebarOverlay.hidden = true;
        sidebarToggle.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('sidebar-open');
        if (restoreFocus) sidebarToggle.focus();
    };
    const openSidebar = () => {
        if (!sidebar || !sidebarToggle || !sidebarOverlay) return;
        sidebar.classList.add('is-open');
        sidebarOverlay.hidden = false;
        sidebarToggle.setAttribute('aria-expanded', 'true');
        document.body.classList.add('sidebar-open');
        const firstLink = sidebar.querySelector('a, button:not([data-sidebar-close])');
        if (firstLink) firstLink.focus();
    };
    if (sidebarToggle) sidebarToggle.addEventListener('click', openSidebar);
    if (sidebarClose) sidebarClose.addEventListener('click', () => closeSidebar({ restoreFocus: true }));
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', () => closeSidebar({ restoreFocus: true }));
    window.addEventListener('resize', () => {
        if (window.innerWidth > 900) closeSidebar();
    });

    document.querySelectorAll('[data-account-menu]').forEach((menu) => {
        const disclosure = setupDisclosure(menu, '[data-account-menu-toggle]', '[data-account-menu-panel]');
        if (!disclosure) return;
        disclosure.toggle.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowDown') {
                event.preventDefault();
                disclosure.open();
                const firstItem = disclosure.panel.querySelector('[role="menuitem"]');
                if (firstItem) firstItem.focus();
            }
        });
    });
    document.querySelectorAll('[data-popover]').forEach((popover) => {
        setupDisclosure(popover, '[data-popover-toggle]', '[data-popover-panel]');
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && sidebar && sidebar.classList.contains('is-open')) {
            closeSidebar({ restoreFocus: true });
        }
    });

    const themeToggle = document.querySelector('[data-theme-toggle]');
    const applyTheme = (theme) => {
        const dark = theme === 'dark';
        document.documentElement.dataset.theme = dark ? 'dark' : 'light';
        if (!themeToggle) return;
        themeToggle.setAttribute('aria-pressed', String(dark));
        themeToggle.setAttribute('aria-label', dark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro');
        const icon = themeToggle.querySelector('[data-theme-icon]');
        if (icon) icon.className = dark ? 'fas fa-sun' : 'fas fa-moon';
    };
    applyTheme(document.documentElement.dataset.theme);
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
            try { window.localStorage.setItem('sgpn-theme', nextTheme); } catch (_error) { /* Storage may be disabled. */ }
            applyTheme(nextTheme);
        });
    }

    const liveRegion = document.querySelector('[data-shell-live-region]');
    let liveRegionTimer;
    document.querySelectorAll('[data-planned-module]').forEach((button) => {
        button.addEventListener('click', () => {
            const moduleName = button.dataset.plannedModule || 'Este módulo';
            const message = `${moduleName} todavía no está disponible.`;
            if (!liveRegion) return;
            window.clearTimeout(liveRegionTimer);
            liveRegion.textContent = message;
            liveRegion.classList.add('is-visible');
            liveRegionTimer = window.setTimeout(() => liveRegion.classList.remove('is-visible'), 4500);
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

    const progress = document.querySelector('[data-navigation-progress]');
    const showProgress = () => { if (progress) progress.classList.add('is-loading'); };
    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[href]');
        if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const target = new URL(link.href, window.location.href);
        const sameDocumentAnchor = target.pathname === window.location.pathname
            && target.search === window.location.search
            && Boolean(target.hash);
        if (target.origin === window.location.origin && target.href !== window.location.href && !sameDocumentAnchor && !link.hasAttribute('download')) showProgress();
    });
    document.addEventListener('submit', (event) => {
        if (event.target instanceof HTMLFormElement) showProgress();
    });

    document.querySelectorAll('.flash-alert').forEach(alert => {
        window.setTimeout(() => {
            alert.classList.add('flash-alert--leaving');
            window.setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

/**
 * Navegación local y accesible para paneles con pestañas.
 * No depende de Alpine ni de recursos externos.
 */

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-tabs]').forEach(inicializarPestanas);
});

function inicializarPestanas(contenedor) {
    const botones = Array.from(contenedor.querySelectorAll('[data-tab-target]'));
    const paneles = Array.from(contenedor.querySelectorAll('[data-tab-panel]'));
    const variante = contenedor.dataset.tabVariant || 'pill';

    if (!botones.length || !paneles.length) return;

    function estilizarBoton(boton, activo) {
        boton.setAttribute('aria-selected', String(activo));
        boton.tabIndex = activo ? 0 : -1;

        if (variante === 'line') {
            boton.classList.toggle('text-teal-600', activo);
            boton.classList.toggle('border-teal-600', activo);
            boton.classList.toggle('border-b-2', activo);
            boton.classList.toggle('text-gray-500', !activo);
            return;
        }

        boton.classList.toggle('bg-teal-600', activo);
        boton.classList.toggle('text-white', activo);
        boton.classList.toggle('bg-gray-100', !activo);
        boton.classList.toggle('text-gray-600', !activo);
    }

    function activarPestana(tabId, moverFoco = false) {
        const botonActivo = botones.find((boton) => boton.dataset.tabTarget === tabId);
        const panelActivo = paneles.find((panel) => panel.dataset.tabPanel === tabId);
        if (!botonActivo || !panelActivo) return;

        botones.forEach((boton) => estilizarBoton(boton, boton === botonActivo));
        paneles.forEach((panel) => {
            const activo = panel === panelActivo;
            panel.hidden = !activo;
            panel.setAttribute('aria-hidden', String(!activo));
        });
        contenedor.dataset.activeTab = tabId;
        if (moverFoco) botonActivo.focus();
    }

    botones.forEach((boton, indice) => {
        boton.addEventListener('click', () => activarPestana(boton.dataset.tabTarget));
        boton.addEventListener('keydown', (evento) => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(evento.key)) return;
            evento.preventDefault();
            let destino = indice;
            if (evento.key === 'ArrowLeft') destino = (indice - 1 + botones.length) % botones.length;
            if (evento.key === 'ArrowRight') destino = (indice + 1) % botones.length;
            if (evento.key === 'Home') destino = 0;
            if (evento.key === 'End') destino = botones.length - 1;
            activarPestana(botones[destino].dataset.tabTarget, true);
        });
    });

    const formulario = contenedor.matches('form') ? contenedor : contenedor.querySelector('form');
    if (formulario) {
        formulario.addEventListener('invalid', (evento) => {
            const panel = evento.target.closest('[data-tab-panel]');
            if (panel) activarPestana(panel.dataset.tabPanel);
        }, true);
    }

    const predeterminada = (
        contenedor.dataset.defaultTab
        || botones.find((boton) => boton.getAttribute('aria-selected') === 'true')?.dataset.tabTarget
        || botones[0].dataset.tabTarget
    );
    activarPestana(predeterminada);
}

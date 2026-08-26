(function initializeClinicalNotes() {
    'use strict';
    const form = document.querySelector('[data-close-clinical-note]');
    form?.addEventListener('submit', async (event) => {
        event.preventDefault();
        const result = await window.confirmarAccion({
            titulo: '¿La nota está completa?',
            mensaje: 'Después de cerrarla ya no podrás cambiar lo escrito. Si más adelante necesitas agregar información, podrás hacerlo mediante una aclaración.',
            textoConfirmar: 'Sí, cerrar nota', textoCancelar: 'Seguir revisando', icono: 'question',
        });
        if (!result.isConfirmed) return;
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        button.textContent = 'Cerrando…';
        form.submit();
    });
    document.querySelectorAll('.clinical-note-addendum-form').forEach((addendumForm) => addendumForm.addEventListener('submit', () => {
        const button = addendumForm.querySelector('button[type="submit"]');
        button.disabled = true;
        button.textContent = 'Guardando…';
    }));
}());

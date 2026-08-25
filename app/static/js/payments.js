document.addEventListener('DOMContentLoaded', () => {
    const confirmPaymentCancellation = async (form) => {
        const folio = form.dataset.paymentFolio || '';
        const title = folio ? `¿Cancelar el pago ${folio}?` : '¿Cancelar este pago?';
        const message = 'El pago no se eliminará. Se conservará en el historial con estado Cancelado para mantener la trazabilidad. Esta acción no se puede deshacer.';

        if (typeof confirmarAccion === 'function') {
            const result = await confirmarAccion({
                titulo: title,
                mensaje: message,
                textoConfirmar: 'Sí, cancelar pago',
                textoCancelar: 'Volver',
                icono: 'warning'
            });
            return Boolean(result.isConfirmed);
        }
        return window.confirm(`${title}\n\n${message}`);
    };

    document.querySelectorAll('[data-payment-form]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            if (form.dataset.submitted === 'true') {
                event.preventDefault();
                return;
            }
            if (!form.checkValidity()) return;
            form.dataset.submitted = 'true';
            const button = form.querySelector('[data-payment-submit]');
            const label = form.querySelector('[data-payment-submit-label]');
            if (button) button.disabled = true;
            if (label) label.textContent = 'Registrando…';
        });
    });

    document.querySelectorAll('[data-payment-cancel-form]').forEach((form) => {
        form.addEventListener('submit', async (event) => {
            if (!form.checkValidity()) return;
            if (form.dataset.confirmed === 'true') return;
            event.preventDefault();
            if (form.dataset.awaitingConfirmation === 'true') return;
            form.dataset.awaitingConfirmation = 'true';
            const confirmed = await confirmPaymentCancellation(form);
            form.dataset.awaitingConfirmation = 'false';
            if (!confirmed) return;

            const button = form.querySelector('button[type="submit"]');
            if (button) {
                button.disabled = true;
                button.textContent = 'Cancelando…';
            }
            form.dataset.confirmed = 'true';
            form.requestSubmit();
        });
    });

    document.addEventListener('click', (event) => {
        document.querySelectorAll('.payment-cancel-menu[open]').forEach((menu) => {
            if (!menu.contains(event.target)) menu.removeAttribute('open');
        });
    });
});

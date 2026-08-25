document.addEventListener('DOMContentLoaded', () => {
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
        form.addEventListener('submit', (event) => {
            if (!form.checkValidity()) return;
            if (!window.confirm('El pago original permanecerá en el historial y no podrá reactivarse. ¿Deseas cancelarlo?')) {
                event.preventDefault();
                return;
            }
            const button = form.querySelector('button[type="submit"]');
            if (button) {
                button.disabled = true;
                button.textContent = 'Cancelando…';
            }
        });
    });

    document.addEventListener('click', (event) => {
        document.querySelectorAll('.payment-cancel-menu[open]').forEach((menu) => {
            if (!menu.contains(event.target)) menu.removeAttribute('open');
        });
    });
});

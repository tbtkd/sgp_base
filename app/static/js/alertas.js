/** Diálogos locales, sin dependencias remotas, compatibles con el uso de Swal. */
(function initializeLocalDialogs() {
    'use strict';

    let validationTarget = null;

    function normalizeOptions(first, second, third) {
        if (typeof first === 'object' && first !== null) return first;
        return { title: first || '', text: second || '', icon: third || 'info' };
    }

    function fire(first, second, third) {
        const options = normalizeOptions(first, second, third);
        return new Promise((resolve) => {
            const dialog = document.createElement('dialog');
            dialog.className = 'sgpn-dialog';
            dialog.setAttribute('aria-labelledby', 'sgpn-dialog-title');
            const card = document.createElement('form');
            card.method = 'dialog';
            card.className = 'sgpn-dialog-card';
            const icon = document.createElement('span');
            icon.className = `sgpn-dialog-icon sgpn-dialog-icon--${options.icon || 'question'}`;
            icon.setAttribute('aria-hidden', 'true');
            icon.textContent = ['error', 'warning'].includes(options.icon) ? '!' : options.icon === 'success' ? '✓' : '?';
            const title = document.createElement('h2');
            title.id = 'sgpn-dialog-title';
            title.textContent = options.title || 'Confirmar acción';
            card.append(icon, title);
            if (options.text) {
                const message = document.createElement('p');
                message.className = 'sgpn-dialog-message';
                message.textContent = options.text;
                card.append(message);
            }
            let input = null;
            if (options.input === 'textarea') {
                const label = document.createElement('label');
                label.className = 'sgpn-dialog-label';
                label.textContent = options.inputLabel || 'Información adicional';
                input = document.createElement('textarea');
                input.className = 'sgpn-dialog-input';
                input.placeholder = options.inputPlaceholder || '';
                input.maxLength = Number(options.inputAttributes?.maxlength || 500);
                input.rows = 4;
                label.append(input);
                card.append(label);
            }
            const validation = document.createElement('p');
            validation.className = 'sgpn-dialog-validation';
            validation.hidden = true;
            card.append(validation);
            validationTarget = validation;
            const actions = document.createElement('div');
            actions.className = 'sgpn-dialog-actions';
            if (options.showCancelButton) {
                const cancel = document.createElement('button');
                cancel.type = 'button';
                cancel.className = 'sgpn-dialog-cancel';
                cancel.textContent = options.cancelButtonText || 'Cancelar';
                cancel.addEventListener('click', () => dialog.close('cancel'));
                actions.append(cancel);
            }
            const confirm = document.createElement('button');
            confirm.type = 'button';
            confirm.className = 'sgpn-dialog-confirm';
            confirm.textContent = options.confirmButtonText || 'Aceptar';
            confirm.addEventListener('click', async () => {
                validation.hidden = true;
                const rawValue = input ? input.value : true;
                const value = options.preConfirm ? await options.preConfirm(rawValue) : rawValue;
                if (value === false) return;
                dialog.dataset.value = typeof value === 'string' ? value : String(rawValue === true ? '' : rawValue);
                dialog.close('confirm');
            });
            actions.append(confirm);
            card.append(actions);
            dialog.append(card);
            dialog.addEventListener('cancel', (event) => {
                event.preventDefault();
                dialog.close('cancel');
            });
            dialog.addEventListener('close', () => {
                const confirmed = dialog.returnValue === 'confirm';
                const value = dialog.dataset.value || '';
                validationTarget = null;
                dialog.remove();
                resolve({ isConfirmed: confirmed, isDismissed: !confirmed, value });
            }, { once: true });
            document.body.append(dialog);
            dialog.showModal();
            (input || confirm).focus();
        });
    }

    const localSwal = {
        fire,
        mixin() { return { fire }; },
        showValidationMessage(message) {
            if (!validationTarget) return;
            validationTarget.textContent = String(message || 'Verifica la información.');
            validationTarget.hidden = false;
        },
    };
    window.Swal = localSwal;
    window.confirmarAccion = ({ titulo, mensaje, textoConfirmar = 'Sí, continuar', textoCancelar = 'Cancelar', icono = 'question' }) => fire({
        title: titulo || '¿Confirmar acción?', text: mensaje || 'Esta acción modificará el registro.', icon: icono,
        showCancelButton: true, confirmButtonText: textoConfirmar, cancelButtonText: textoCancelar,
    });
    window.mostrarAlerta = (titulo, mensaje, icono = 'success') => fire({ title: titulo, text: mensaje, icon: icono });
}());

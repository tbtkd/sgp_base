(function () {
    'use strict';

    const form = document.querySelector('[data-prescription-form]');
    if (!form) return;
    const list = form.querySelector('[data-medicine-list]');
    const add = form.querySelector('[data-add-medicine]');
    const template = document.getElementById('medicine-row-template');

    function renumber() {
        list.querySelectorAll('.medicine-row').forEach((row, index) => {
            const number = row.querySelector('[data-medicine-number]');
            if (number) number.textContent = String(index + 1);
            const remove = row.querySelector('[data-remove-medicine]');
            if (remove) remove.disabled = list.querySelectorAll('.medicine-row').length === 1;
        });
        if (add) add.disabled = list.querySelectorAll('.medicine-row').length >= 10;
    }

    list.addEventListener('click', function (event) {
        const button = event.target.closest('[data-remove-medicine]');
        if (!button) return;
        const rows = list.querySelectorAll('.medicine-row');
        if (rows.length > 1) button.closest('.medicine-row').remove();
        renumber();
    });

    if (add && template) {
        add.addEventListener('click', function () {
            if (list.querySelectorAll('.medicine-row').length >= 10) return;
            list.appendChild(template.content.cloneNode(true));
            renumber();
        });
    }
    form.addEventListener('submit', function (event) {
        if (form.dataset.submitting === 'true') {
            event.preventDefault();
            return;
        }
        if (!form.checkValidity()) return;
        form.dataset.submitting = 'true';
        const submit = form.querySelector('button[type="submit"]');
        if (submit) {
            submit.disabled = true;
            submit.textContent = 'Emitiendo…';
        }
    });
    renumber();
})();

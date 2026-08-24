(function () {
    'use strict';

    const form = document.querySelector('[data-prescription-form]');
    if (!form) return;
    const list = form.querySelector('[data-medicine-list]');
    const add = form.querySelector('[data-add-medicine]');
    const template = document.getElementById('medicine-row-template');

    function medicineRows() {
        return Array.from(list.querySelectorAll('.medicine-row'));
    }

    function captureOrder(row) {
        const input = row.querySelector('[data-medicine-order-input]');
        const value = Number.parseInt(input ? input.value : row.dataset.medicineOrder, 10);
        return Number.isInteger(value) && value > 0 ? value : Number.MAX_SAFE_INTEGER;
    }

    function renumber() {
        const rows = medicineRows();
        const ordered = rows.slice().sort((left, right) => captureOrder(left) - captureOrder(right));
        ordered.forEach((row, index) => {
            const value = String(index + 1);
            row.dataset.medicineOrder = value;
            const orderInput = row.querySelector('[data-medicine-order-input]');
            if (orderInput) orderInput.value = value;
            const number = row.querySelector('[data-medicine-number]');
            if (number) number.textContent = value;
            const remove = row.querySelector('[data-remove-medicine]');
            if (remove) remove.disabled = rows.length === 1;
        });
        if (add) add.disabled = rows.length >= 10;
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
            const rows = medicineRows();
            if (rows.length >= 10) return;
            const nextOrder = Math.max(0, ...rows.map(captureOrder).filter(Number.isFinite)) + 1;
            const fragment = template.content.cloneNode(true);
            const newRow = fragment.querySelector('.medicine-row');
            const orderInput = newRow.querySelector('[data-medicine-order-input]');
            newRow.dataset.medicineOrder = String(nextOrder);
            if (orderInput) orderInput.value = String(nextOrder);
            list.prepend(fragment);
            renumber();
            const firstRequired = newRow.querySelector('input[required]');
            if (firstRequired) firstRequired.focus();
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

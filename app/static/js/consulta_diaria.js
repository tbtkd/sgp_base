(function () {
    'use strict';

    const form = document.querySelector('[data-daily-consultation-form]');
    if (!form) return;

    const dateInput = form.querySelector('#fecha');
    const numberInput = form.querySelector('#numero_cita');
    const status = form.querySelector('[data-daily-number-status]');
    const endpoint = form.dataset.dailyNumberUrl;
    let activeRequest = null;

    function setStatus(message, isError) {
        if (!status) return;
        status.textContent = message;
        status.classList.toggle('text-red-600', Boolean(isError));
        status.classList.toggle('text-teal-700', !isError);
    }

    async function refreshNumber() {
        const selectedDate = dateInput ? dateInput.value : '';
        if (!selectedDate || !endpoint || !numberInput) return;

        if (selectedDate === form.dataset.currentDate && form.dataset.currentNumber) {
            numberInput.value = form.dataset.currentNumber;
            setStatus('Turno actual conservado para esta fecha.', false);
            return;
        }

        if (activeRequest) activeRequest.abort();
        activeRequest = new AbortController();
        setStatus('Consultando el siguiente turno disponible…', false);
        try {
            const url = new URL(endpoint, window.location.origin);
            url.searchParams.set('fecha', selectedDate);
            const response = await fetch(url.toString(), {
                cache: 'no-store',
                credentials: 'same-origin',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                signal: activeRequest.signal,
            });
            const payload = await response.json();
            if (!response.ok || !payload.success) throw new Error(payload.error || 'Consulta no disponible');
            numberInput.value = String(payload.numero);
            setStatus(`Siguiente turno proyectado: ${payload.numero}.`, false);
        } catch (error) {
            if (error.name === 'AbortError') return;
            setStatus('No pudimos mostrar el siguiente turno. Al guardar, el sistema asignará el turno correcto.', true);
        }
    }

    if (dateInput) dateInput.addEventListener('change', refreshNumber);
    refreshNumber();
})();

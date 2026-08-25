/** Interacciones locales de la Agenda operativa. */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-agenda-workspace]').forEach(initializeAgenda);
});

function initializeAgenda(root) {
    const allowedStatuses = new Set(['Atendida', 'No Asistió', 'Cancelada']);
    const liveRegion = root.querySelector('[data-agenda-live]');
    const pendingRequests = new Set();

    function announce(message) {
        if (!liveRegion) return;
        liveRegion.textContent = String(message || '');
        window.setTimeout(() => {
            if (liveRegion.textContent === message) liveRegion.textContent = '';
        }, 4500);
    }

    async function askForStatus(status) {
        if (window.Swal) {
            const requiresReason = status === 'Cancelada';
            const result = await window.Swal.fire({
                title: status === 'Atendida'
                    ? '¿Marcar la cita como atendida?'
                    : status === 'No Asistió'
                        ? '¿Registrar la inasistencia?'
                        : '¿Cancelar esta cita?',
                text: status === 'Atendida' ? 'La cita quedará cerrada y ya no podrá reagendarse.' : undefined,
                input: status === 'Atendida' ? undefined : 'textarea',
                inputLabel: status === 'Cancelada' ? 'Motivo de cancelación' : 'Observaciones (opcional)',
                inputPlaceholder: status === 'Atendida' ? undefined : 'Escribe una referencia breve…',
                inputAttributes: status === 'Atendida' ? undefined : { maxlength: '500' },
                icon: status === 'Atendida' ? 'question' : 'warning',
                showCancelButton: true,
                confirmButtonColor: '#0d9488',
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Confirmar',
                cancelButtonText: 'Volver',
                preConfirm: (value) => {
                    const reason = String(value || '').trim();
                    if (requiresReason && !reason) {
                        window.Swal.showValidationMessage('El motivo de cancelación es obligatorio.');
                        return false;
                    }
                    return reason;
                },
            });
            return result.isConfirmed ? { confirmed: true, reason: String(result.value || '').trim() } : { confirmed: false };
        }

        if (!window.confirm(`¿Confirmar el estado “${status}”?`)) return { confirmed: false };
        const reason = status === 'Atendida' ? '' : String(window.prompt('Motivo u observaciones:', '') || '').trim();
        if (status === 'Cancelada' && !reason) {
            announce('El motivo de cancelación es obligatorio.');
            return { confirmed: false };
        }
        return { confirmed: true, reason };
    }

    function updateCount(status, delta) {
        const counter = root.querySelector(`[data-status-count="${status}"]`);
        if (!counter) return;
        const current = Number.parseInt(counter.textContent, 10) || 0;
        counter.textContent = String(Math.max(0, current + delta));
    }

    function renderClosedRow(row, status) {
        const currentStatus = row.dataset.currentStatus || 'Programada';
        updateCount(currentStatus, -1);
        updateCount(status, 1);
        row.dataset.currentStatus = status;

        const badge = row.querySelector('[data-appointment-status]');
        if (badge) {
            const statusClass = status.toLowerCase().replaceAll(' ', '-').replaceAll('ó', 'o');
            badge.className = `agenda-status agenda-status--${statusClass}`;
            badge.textContent = status;
        }
        const actions = row.querySelector('[data-appointment-actions]');
        if (actions) actions.remove();
    }

    async function updateAppointment(button) {
        const status = button.dataset.appointmentStatusAction;
        const url = button.dataset.statusUrl;
        const row = button.closest('[data-appointment-row]');
        if (!allowedStatuses.has(status) || !url || !row || pendingRequests.has(row)) return;

        const decision = await askForStatus(status);
        if (!decision.confirmed) return;

        pendingRequests.add(row);
        row.setAttribute('aria-busy', 'true');
        row.querySelectorAll('button').forEach((item) => { item.disabled = true; });
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                body: JSON.stringify({ estatus: status, motivo: decision.reason || '' }),
            });
            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.error || 'No fue posible actualizar la cita.');
            renderClosedRow(row, data.nuevo_estatus);
            announce(`Cita actualizada: ${data.nuevo_estatus}.`);
        } catch (error) {
            row.querySelectorAll('button').forEach((item) => { item.disabled = false; });
            const message = error.message || 'No fue posible actualizar la cita.';
            announce(message);
            if (window.Swal) await window.Swal.fire('No fue posible actualizar', message, 'error');
        } finally {
            pendingRequests.delete(row);
            row.removeAttribute('aria-busy');
        }
    }

    root.querySelectorAll('[data-appointment-status-action]').forEach((button) => {
        button.addEventListener('click', () => updateAppointment(button));
    });
}

/**
 * dashboard.js - Lógica de interacción para el Dashboard Clínico (Modales, WhatsApp, Seguimientos)
 */

let currentValId = null;
let currentTelefono = null;

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-dashboard-appointment]').forEach((button) => {
        button.addEventListener('click', () => marcarEstatusCita(button.dataset.dashboardAppointment, button.dataset.dashboardStatus));
    });
    document.querySelectorAll('[data-postpone-followup]').forEach((button) => button.addEventListener('click', () => omitirSeguimiento(button.dataset.postponeFollowup)));
    document.querySelectorAll('[data-open-whatsapp]').forEach((button) => button.addEventListener('click', () => abrirModalWhatsAppDesdeBoton(button)));
    document.querySelectorAll('[data-close-postpone]').forEach((button) => button.addEventListener('click', cerrarModalOmitir));
    document.querySelectorAll('[data-confirm-postpone]').forEach((button) => button.addEventListener('click', confirmarOmitirSeguimiento));
    document.querySelectorAll('[data-copy-whatsapp]').forEach((button) => button.addEventListener('click', copiarTextoModal));
    document.querySelectorAll('[data-close-whatsapp]').forEach((button) => button.addEventListener('click', cerrarModalWhatsApp));
    document.querySelectorAll('[data-send-whatsapp]').forEach((button) => button.addEventListener('click', confirmarEnviarWhatsApp));
    document.querySelectorAll('[data-dashboard-charts]').forEach((chartGroup) => {
        const tabs = Array.from(chartGroup.querySelectorAll('[data-dashboard-chart-tab]'));
        const panels = Array.from(chartGroup.querySelectorAll('[data-dashboard-chart-panel]'));
        const activate = (tab) => {
            const target = tab.dataset.dashboardChartTab;
            tabs.forEach((item) => item.setAttribute('aria-selected', String(item === tab)));
            panels.forEach((panel) => { panel.hidden = panel.dataset.dashboardChartPanel !== target; });
            tab.focus();
        };
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => activate(tab));
            tab.addEventListener('keydown', (event) => {
                if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
                event.preventDefault();
                let nextIndex = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : index;
                if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
                if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
                activate(tabs[nextIndex]);
            });
        });
    });
});

async function marcarEstatusCita(citaId, nuevoEstatus) {
    const allowedStatuses = new Set(['No Asistió', 'Cancelada']);
    if (!allowedStatuses.has(nuevoEstatus)) return;

    const title = nuevoEstatus === 'No Asistió'
        ? '¿Marcar como no asistió?'
        : '¿Cancelar esta cita?';
    const result = await Swal.fire({
        title,
        input: 'textarea',
        inputLabel: 'Motivo u observaciones (opcional)',
        inputPlaceholder: 'Describe brevemente el motivo…',
        inputAttributes: { maxlength: '500' },
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#0d9488',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Confirmar',
        cancelButtonText: 'Volver',
    });
    if (!result.isConfirmed) return;

    try {
        const response = await fetch(`/pacientes/citas/${citaId}/cambiar-estatus`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ estatus: nuevoEstatus, motivo: result.value || '' }),
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'No fue posible actualizar la cita.');
        }

        const actions = document.getElementById(`acciones-cita-${citaId}`);
        if (actions) {
            const badge = document.createElement('span');
            badge.className = nuevoEstatus === 'No Asistió'
                ? 'dashboard-status dashboard-status--no-asistio'
                : 'dashboard-status dashboard-status--cancelada';
            badge.textContent = nuevoEstatus;
            actions.replaceChildren(badge);
        }
        mostrarToast(`Cita actualizada: ${nuevoEstatus}.`);
    } catch (error) {
        console.error('Error al actualizar la cita:', error);
        await Swal.fire('No fue posible actualizar', error.message, 'error');
    }
}

function formatearTelefonoMexico(telefono) {
    if (!telefono) return '';
    let telClean = telefono.replace(/[^0-9]/g, '');
    if (telClean.length === 10) {
        telClean = '52' + telClean;
    } else if (telClean.length === 12 && telClean.startsWith('52')) {
        // Correcto
    }
    return telClean;
}

function abrirModalWhatsAppDesdeBoton(btn) {
    const valId = btn.getAttribute('data-val-id');
    const telefono = btn.getAttribute('data-telefono');
    const nombrePaciente = btn.getAttribute('data-nombre');
    const diasTranscurridos = btn.getAttribute('data-dias');
    abrirModalWhatsApp(valId, telefono, nombrePaciente, diasTranscurridos);
}

function abrirModalWhatsApp(valId, telefono, nombrePaciente, diasTranscurridos) {
    if (!telefono) {
        alert('El paciente no tiene un número de teléfono registrado.');
        return;
    }

    currentValId = valId;
    currentTelefono = formatearTelefonoMexico(telefono);

    if (!currentTelefono) {
        alert('El número de teléfono del paciente no es válido.');
        return;
    }

    const configElement = document.getElementById('data-config');
    const plantillaRaw = configElement ? configElement.getAttribute('data-plantilla') : null;
    const dashboardPlantillaActiva = plantillaRaw && plantillaRaw !== 'null' ? JSON.parse(plantillaRaw) : null;

    const plantillaTemplate = dashboardPlantillaActiva || "Hola, {nombre}. Han pasado {dias} días desde tu última consulta. Queremos saber cómo continúa tu evolución y si necesitas agendar una revisión.";
    
    const mensajeBase = plantillaTemplate
        .replace('{nombre}', nombrePaciente)
        .replace('{dias}', diasTranscurridos);

    const subElement = document.getElementById('modalPacienteSub');
    if (subElement) {
        subElement.textContent = `Paciente: ${nombrePaciente}`;
    }
    
    const textareaElement = document.getElementById('modalMensajeTexto');
    if (textareaElement) {
        textareaElement.value = mensajeBase;
    }

    const modal = document.getElementById('modalWhatsApp');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function cerrarModalWhatsApp() {
    const modal = document.getElementById('modalWhatsApp');
    if (modal) {
        modal.classList.add('hidden');
    }
    currentValId = null;
    currentTelefono = null;
}

function mostrarToast(mensaje, tipo = 'success') {
    let toast = document.getElementById('appToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'appToast';
        toast.className = 'fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border text-sm font-medium transition-all duration-300 transform translate-y-20 opacity-0';
        document.body.appendChild(toast);
    }
    
    toast.className = 'fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border bg-gray-900 text-white border-gray-800 transition-all duration-300 transform translate-y-20 opacity-0';
    
    const iconClass = tipo === 'success' ? 'fa-check' : 'fa-exclamation';
    const colorClass = tipo === 'success' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400';
    toast.replaceChildren();
    const iconBox = document.createElement('div');
    iconBox.className = `w-8 h-8 rounded-xl ${colorClass} flex items-center justify-center shrink-0`;
    const icon = document.createElement('i');
    icon.className = `fas ${iconClass}`;
    iconBox.appendChild(icon);
    const label = document.createElement('span');
    label.textContent = String(mensaje || '');
    toast.append(iconBox, label);

    setTimeout(() => {
        toast.classList.remove('translate-y-20', 'opacity-0');
    }, 10);

    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 3000);
}

function copiarTextoModal() {
    const textarea = document.getElementById('modalMensajeTexto');
    if (!textarea) return;
    textarea.select();
    navigator.clipboard.writeText(textarea.value).then(() => {
        mostrarToast('¡Texto copiado al portapapeles con éxito!');
    }).catch(err => {
        console.error('Error al copiar al portapapeles:', err);
        mostrarToast('No se pudo copiar el texto automáticamente.', 'error');
    });
}

let valIdParaOmitir = null;

function omitirSeguimiento(valId) {
    valIdParaOmitir = valId;
    const modal = document.getElementById('modalOmitirSeguimiento');
    if (modal) modal.classList.remove('hidden');
}

function cerrarModalOmitir() {
    const modal = document.getElementById('modalOmitirSeguimiento');
    if (modal) modal.classList.add('hidden');
    valIdParaOmitir = null;
}

function confirmarOmitirSeguimiento() {
    if (!valIdParaOmitir) return;
    const valId = valIdParaOmitir;
    cerrarModalOmitir();

    const row = document.getElementById(`row-val-${valId}`);
    if (row) {
        const actionTd = row.querySelector('td:last-child');
        if (actionTd) {
            actionTd.innerHTML = `<span class="bg-amber-100 text-amber-800 text-xs px-3 py-1 rounded-full font-semibold flex items-center gap-1 justify-end ml-auto"><i class="fas fa-clock"></i> Omitido</span>`;
        }
        row.classList.add('opacity-50');
    }

    fetch(`/dashboard/omitir-seguimiento/${valId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Error al omitir seguimiento:', data.message);
            alert('No fue posible guardar el seguimiento. Inténtalo de nuevo.');
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error en la petición AJAX:', error);
        alert('No hay conexión en este momento. Revisa tu conexión e inténtalo de nuevo.');
        location.reload();
    });
}

function confirmarEnviarWhatsApp() {
    if (!currentValId || !currentTelefono) return;

    const textarea = document.getElementById('modalMensajeTexto');
    const mensajeEditado = textarea ? textarea.value : '';
    const urlWa = `https://wa.me/${currentTelefono}?text=${encodeURIComponent(mensajeEditado)}`;

    const valIdToProcess = currentValId;
    const row = document.getElementById(`row-val-${valIdToProcess}`);
    if (row) {
        const actionTd = row.querySelector('td:last-child');
        if (actionTd) {
            actionTd.innerHTML = `<span class="bg-green-100 text-green-800 text-xs px-3 py-1 rounded-full font-semibold flex items-center gap-1 justify-end ml-auto"><i class="fas fa-check-circle"></i> Contactado</span>`;
        }
        row.classList.add('opacity-75');
    }
    cerrarModalWhatsApp();

    const waWindow = window.open(urlWa, '_blank', 'noopener,noreferrer');
    if (waWindow) waWindow.opener = null;

    fetch(`/dashboard/marcar-seguimiento/${valIdToProcess}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mensaje: mensajeEditado })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Error al registrar estatus:', data.message);
            alert('Error al registrar el estatus en el sistema.');
        }
    })
    .catch(error => {
        console.error('Error en la petición AJAX:', error);
    });
}

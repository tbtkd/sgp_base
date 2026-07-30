/**
 * dashboard.js - Lógica de interacción para el Dashboard Clínico (Modales, WhatsApp, Seguimientos)
 */

let currentValId = null;
let currentTelefono = null;

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

    const plantillaTemplate = window.dashboardPlantillaActiva || "¡Hola, {nombre}! 👋 Te saluda la nutrióloga Aurora Ángeles. Han pasado {dias} días desde tu última consulta y quería saber cómo te has sentido con tu plan de alimentación y si te ha surgido alguna duda. ¡Sigo al pendiente de tus avances!";
    
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
    
    toast.innerHTML = `<div class="w-8 h-8 rounded-xl ${colorClass} flex items-center justify-center shrink-0"><i class="fas ${iconClass}"></i></div><span>${mensaje}</span>`;

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
            alert('Error al registrar en el servidor.');
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error en la petición AJAX:', error);
        alert('Error de red.');
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

    window.open(urlWa, '_blank');

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

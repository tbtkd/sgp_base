function enviarExcel(event) {
    const form = event.target;
    const fileInput = form.querySelector('input[name="file"]');
    if (!fileInput.files || fileInput.files.length === 0) {
        // Alpine component error handling
        form.__x.$data.error = 'Por favor, selecciona un archivo Excel antes de cargar.';
        return;
    }

    const formData = new FormData(form);
    
    // Ocultar modal de carga actual
    const modalContainer = document.getElementById('formCargarExcel').closest('[x-data]');
    if (modalContainer && modalContainer.__x) {
        modalContainer.__x.$data.modalExcelOpen = false;
    }

    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        mostrarModalResultadoCarga(data);
    })
    .catch(error => {
        mostrarModalResultadoCarga({
            success: false,
            message: 'Ocurrió un error al procesar la solicitud: ' + error,
            registros_procesados: 0,
            registros_duplicados: 0,
            errores: [error.toString()]
        });
    });
}

function mostrarModalResultadoCarga(data) {
    const modal = document.getElementById('modalResultadoCarga');
    const mensajeEl = document.getElementById('modalResultadoMensaje');
    const statProcesados = document.getElementById('statProcesados');
    const statDuplicados = document.getElementById('statDuplicados');
    const contenedorErrores = document.getElementById('contenedorErroresModal');
    const listaErrores = document.getElementById('listaErroresModal');
    const header = document.getElementById('modalResultadoHeader');
    const titulo = document.getElementById('modalResultadoTitulo');
    const icono = document.getElementById('modalResultadoIcono');

    if (!modal) return;

    mensajeEl.textContent = data.message || '';
    statProcesados.textContent = data.registros_procesados || 0;
    statDuplicados.textContent = data.registros_duplicados || 0;

    // Manejo de errores u observaciones
    listaErrores.innerHTML = '';
    if (data.errores && Array.isArray(data.errores) && data.errores.length > 0) {
        contenedorErrores.classList.remove('hidden');
        data.errores.forEach(err => {
            const div = document.createElement('div');
            div.textContent = err;
            listaErrores.appendChild(div);
        });
    } else if (typeof data.errores === 'string' && data.errores !== 'No se encontraron errores.' && data.errores.trim() !== '') {
        contenedorErrores.classList.remove('hidden');
        const div = document.createElement('div');
        div.textContent = data.errores;
        listaErrores.appendChild(div);
    } else {
        contenedorErrores.classList.add('hidden');
    }

    // Estilos según éxito o fallo
    if (data.success) {
        header.className = 'px-6 py-4 flex justify-between items-center bg-emerald-600 text-white';
        icono.className = 'fas fa-check-circle';
        titulo.querySelector('span').textContent = 'Procesamiento Exitoso';
    } else {
        header.className = 'px-6 py-4 flex justify-between items-center bg-rose-600 text-white';
        icono.className = 'fas fa-exclamation-triangle';
        titulo.querySelector('span').textContent = 'Aviso / Error en Carga';
    }

    modal.classList.remove('hidden');
}

function cerrarModalResultadoCarga() {
    const modal = document.getElementById('modalResultadoCarga');
    if (modal) {
        modal.classList.add('hidden');
    }
    window.location.reload();
}

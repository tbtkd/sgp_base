/**
 * Valida el formulario de Historial Clínico.
 * Maneja la navegación entre pestañas de Alpine.js si hay errores.
 */
export function validarFormularioHistorialClinico() {
    const tabsConfig = {
        'actividad-fisica': 'Actividad Física',
        'alimentacion': 'Alimentación',
        'historial-medico': 'Historial Médico'
    };

    // Campos obligatorios
    const campos = [
        { id: 'tipo_actividad_fisica', label: 'Tipo de actividad física', tab: 'actividad-fisica' },
        { id: 'frecuencia_actividad_fisica', label: 'Frecuencia de actividad física', tab: 'actividad-fisica' },
        { id: 'tiempo_actividad_fisica', label: 'Tiempo de actividad física', tab: 'actividad-fisica' },
        { id: 'numero_comidas_diarias', label: 'Número de comidas diarias', tab: 'alimentacion' }
    ];

    let primerError = null;

    // Limpiar errores previos
    campos.forEach(campo => {
        const el = document.getElementById(campo.id);
        if (el) {
            el.classList.remove('is-invalid');
            const group = el.closest('.form-group');
            if (group) {
                const errorSpan = group.querySelector('.error-message');
                if (errorSpan) errorSpan.style.display = 'none';
            }
        }
    });

    // Validar secuencialmente
    for (const campo of campos) {
        const el = document.getElementById(campo.id);
        if (!el) continue;

        if (el.value.trim() === "") {
            primerError = campo;
            el.classList.add('is-invalid');
            const group = el.closest('.form-group');
            if (group) {
                const errorSpan = group.querySelector('.error-message');
                if (errorSpan) errorSpan.style.display = 'block';
            }
            break;
        }
    }

    if (primerError) {
        const nombreTab = tabsConfig[primerError.tab];
        
        // Cambiar pestaña: Simular clic en el botón de la pestaña correspondiente
        // Buscamos el botón que contiene el texto de la pestaña o tiene el evento click
        const botonesPestana = document.querySelectorAll('.form-tab');
        botonesPestana.forEach(btn => {
            // Verificamos si el botón corresponde a la pestaña del error
            // Como no tenemos un atributo 'data-tab', buscamos por el texto o lógica de Alpine
            if (btn.getAttribute('@click') && btn.getAttribute('@click').includes(primerError.tab)) {
                btn.click();
            }
        });

        setTimeout(() => {
            const el = document.getElementById(primerError.id);
            if (el) {
                el.focus();
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 150);

        mostrarNotificacion(`Por favor, complete el campo ${primerError.label} en la pestaña ${nombreTab}`, 'error');
        return false;
    }

    return true;
}

function mostrarNotificacion(mensaje, tipo) {
    const alertBanner = document.getElementById('validation-alert');
    const alertText = document.getElementById('validation-alert-text');
    
    if (alertBanner && alertText) {
        alertText.textContent = mensaje;
        alertBanner.style.display = 'flex';
        alertBanner.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        alert(mensaje);
    }
}

export function validarFormularioPaciente(form) {
    const campos = [
        { id: 'nombre', label: 'Nombre' },
        { id: 'apellido_paterno', label: 'Apellido Paterno' },
        { id: 'apellido_materno', label: 'Apellido Materno' },
        { id: 'fecha_nacimiento', label: 'Fecha de Nacimiento' },
        { id: 'telefono', label: 'Teléfono' },
        { id: 'correo', label: 'Correo Electrónico' },
        { id: 'ciudad', label: 'Ciudad' }
    ];

    let primerError = null;

    // Limpiar errores previos
    campos.forEach(campo => {
        const el = document.getElementById(campo.id);
        if (el) {
            el.classList.remove('input-error');
            const group = el.closest('.space-y-2');
            if (group) {
                const errorSpan = group.querySelector('.error-message');
                if (errorSpan) errorSpan.remove();
            }
        }
    });

    // Validar campos
    for (const campo of campos) {
        const el = document.getElementById(campo.id);
        if (!el) continue;

        const valor = el.value.trim();
        let mensajeError = "";

        if (valor === "") {
            mensajeError = `Por favor, ingrese ${campo.label.toLowerCase()}.`;
        } else if (campo.id === 'nombre' && !validarTexto(valor, 3, 30)) {
            mensajeError = "El nombre debe tener entre 3 y 30 caracteres.";
        } else if ((campo.id === 'apellido_paterno' || campo.id === 'apellido_materno') && !validarTexto(valor, 2, 40)) {
            mensajeError = "El apellido debe tener entre 2 y 40 caracteres.";
        } else if (campo.id === 'ciudad' && !validarTexto(valor, 3, 50)) {
            mensajeError = "La ciudad debe tener entre 3 y 50 caracteres.";
        } else if (campo.id === 'fecha_nacimiento' && !validarFechaNacimiento(valor)) {
            mensajeError = "La fecha de nacimiento no es válida (debe ser posterior a 1900 y anterior a hoy).";
        } else if (campo.id === 'telefono' && !validarTelefono(valor)) {
            mensajeError = "El número de teléfono debe tener exactamente 10 dígitos.";
        } else if (campo.id === 'correo' && !validarCorreo(valor)) {
            mensajeError = "El correo electrónico ingresado no parece ser válido.";
        }

        if (mensajeError) {
            primerError = { id: campo.id, mensaje: mensajeError };
            
            // Marcar error
            el.classList.add('input-error');
            const group = el.closest('.space-y-2');
            if (group) {
                const errorSpan = document.createElement("small");
                errorSpan.className = "text-red-600 error-message";
                errorSpan.style.display = "block";
                errorSpan.innerText = mensajeError;
                group.appendChild(errorSpan);
            }
            break; // Solo marcar el primero
        }
    }

    if (primerError) {
        const el = document.getElementById(primerError.id);
        if (el) {
            el.focus();
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return false;
    }

    return true;
}

function validarFechaNacimiento(fecha) {
    const hoy = new Date();
    const fechaNacimiento = new Date(fecha);
    const fechaMinima = new Date('1900-01-01');
    return fechaNacimiento >= fechaMinima && fechaNacimiento < hoy;
}

function validarTelefono(telefono) {
    const regex = /^\d{10}$/;
    return regex.test(telefono);
}

function validarCorreo(correo) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(correo);
}

function validarTexto(texto, min, max) {
    const regex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
    return regex.test(texto) && texto.length >= min && texto.length <= max;
}

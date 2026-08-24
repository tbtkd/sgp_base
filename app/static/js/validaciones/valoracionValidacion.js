export function validarFormularioValoracion() {
    const fecha = document.getElementById("fecha") ? document.getElementById("fecha").value.trim() : "";
    if (!fecha) {
        alert("Por favor seleccione la fecha de la consulta.");
        return false;
    }

    const camposNumericos = ["peso", "estatura", "temperatura", "frecuencia_cardiaca", "frecuencia_respiratoria", "saturacion_oxigeno"];
    for (const campo of camposNumericos) {
        const el = document.getElementById(campo);
        if (el && el.value.trim() !== "") {
            const val = parseFloat(el.value);
            if (isNaN(val) || val < 0) {
                alert(`El valor ingresado en ${campo} debe ser un número positivo.`);
                return false;
            }
        }
    }

    return true;
}

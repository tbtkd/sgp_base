/**
 * Configuración personalizada de SweetAlert2 alineada a la UI/UX de SGPN
 */
const SwalCustom = Swal.mixin({
  customClass: {
    popup: 'rounded-2xl shadow-2xl p-6 border border-gray-100 bg-white',
    title: 'text-xl font-bold text-gray-800 tracking-tight',
    htmlContainer: 'text-sm text-gray-600 font-medium mt-2',
    confirmButton: 'px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm rounded-xl shadow transition-colors mx-2 focus:outline-none cursor-pointer',
    cancelButton: 'px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold text-sm rounded-xl transition-colors mx-2 focus:outline-none cursor-pointer'
  },
  buttonsStyling: false
});

/**
 * Función global para reemplazar el confirm() nativo
 */
function confirmarAccion({ titulo, mensaje, textoConfirmar = 'Sí, continuar', textoCancelar = 'Cancelar', icono = 'question' }) {
  return SwalCustom.fire({
    title: titulo || '¿Estás seguro?',
    text: mensaje || 'Esta acción modificará el registro.',
    icon: icono,
    iconColor: '#059669', // Verde esmeralda
    showCancelButton: true,
    confirmButtonText: textoConfirmar,
    cancelButtonText: textoCancelar,
    reverseButtons: true
  });
}

/**
 * Función auxiliar para notificaciones rápidas tipo toast o alert
 */
function mostrarAlerta(titulo, mensaje, icono = 'success') {
  return SwalCustom.fire({
    title: titulo,
    text: mensaje,
    icon: icono,
    iconColor: icono === 'success' ? '#059669' : '#dc2626',
    confirmButtonText: 'Aceptar'
  });
}

/**
 * detalle_paciente.js - Lógica para el detalle de paciente, modales de Excel, Cita y Bitácora de WhatsApp
 */

document.addEventListener('DOMContentLoaded', () => {
    const btnExcel = document.getElementById('btnOpenExcelModal');
    if (btnExcel) {
        btnExcel.addEventListener('click', () => {
            window.dispatchEvent(new CustomEvent('open-excel-modal'));
        });
    }

    const btnCita = document.getElementById('btnOpenModal');
    if (btnCita) {
        btnCita.addEventListener('click', () => {
            window.dispatchEvent(new CustomEvent('open-cita-modal'));
        });
    }
});

function abrirBitacoraWhatsApp() {
    const modal = document.getElementById('modal-bitacora-whatsapp');
    if (modal) modal.classList.remove('hidden');
}

function cerrarBitacoraWhatsApp() {
    const modal = document.getElementById('modal-bitacora-whatsapp');
    if (modal) modal.classList.add('hidden');
}

function citaForm(fechaInicial = '') {
    return {
        fecha: fechaInicial,
        hora: '',
        horasOcupadas: [],
        init() {
            if (this.fecha) {
                this.actualizarDisponibilidad();
            }
        },
        async actualizarDisponibilidad() {
            if (!this.fecha) return;
            try {
                const response = await fetch(`/pacientes/disponibilidad_horas?fecha=${this.fecha}`);
                this.horasOcupadas = await response.json();
            } catch (err) {
                console.error('Error al obtener disponibilidad:', err);
            }
        }
    }
}



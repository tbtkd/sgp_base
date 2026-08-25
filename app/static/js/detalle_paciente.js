/**
 * detalle_paciente.js - Interacciones locales del detalle del paciente.
 *
 * El modal de citas no depende de Alpine/CDN: permanece cerrado al cargar,
 * conserva cierres accesibles aun si falla la consulta de disponibilidad y
 * evita enviar el formulario más de una vez.
 */

document.addEventListener('DOMContentLoaded', () => {
    const btnExcel = document.getElementById('btnOpenExcelModal');
    if (btnExcel) {
        btnExcel.addEventListener('click', () => {
            const modal = document.getElementById('modalExcel');
            if (modal) modal.hidden = false;
        });
    }

    document.querySelectorAll('[data-close-excel]').forEach((button) => button.addEventListener('click', () => {
        const modal = document.getElementById('modalExcel');
        if (modal) modal.hidden = true;
    }));
    document.querySelectorAll('[data-open-contact-log]').forEach((button) => button.addEventListener('click', abrirBitacoraWhatsApp));
    document.querySelectorAll('[data-close-contact-log]').forEach((button) => button.addEventListener('click', cerrarBitacoraWhatsApp));

    inicializarModalCita();
});

function abrirBitacoraWhatsApp() {
    const modal = document.getElementById('modal-bitacora-whatsapp');
    if (modal) modal.classList.remove('hidden');
}

function cerrarBitacoraWhatsApp() {
    const modal = document.getElementById('modal-bitacora-whatsapp');
    if (modal) modal.classList.add('hidden');
}

function inicializarModalCita() {
    const botonAbrir = document.getElementById('btnOpenModal');
    const modalCita = document.getElementById('modalCita');
    const modalAdvertencia = document.getElementById('modalAdvertenciaCita');
    const formulario = document.getElementById('formProximaCita');
    const fecha = document.getElementById('proxima_cita_fecha');
    const hora = document.getElementById('proxima_cita_hora');
    const estado = document.getElementById('estadoDisponibilidad');
    const error = document.getElementById('errorDisponibilidad');
    const botonGuardar = document.getElementById('btnGuardarCita');
    const textoGuardar = document.getElementById('textoGuardarCita');

    if (!botonAbrir || !modalCita || !formulario || !fecha || !hora || !botonGuardar) {
        return;
    }

    const tieneCita = modalCita.dataset.tieneCita === 'true';
    const fechaInicial = modalCita.dataset.fechaInicial || '';
    const horaInicial = modalCita.dataset.horaInicial || '';
    const citaId = modalCita.dataset.citaId || '';
    const disponibilidadUrl = modalCita.dataset.disponibilidadUrl || '';
    const textoGuardarInicial = textoGuardar ? textoGuardar.textContent : 'Agendar';
    let solicitudDisponibilidad = null;
    let enviando = false;

    const modales = [modalCita, modalAdvertencia].filter(Boolean);

    function sincronizarBloqueoPagina() {
        const hayModalVisible = modales.some((modal) => !modal.hidden);
        document.body.classList.toggle('modal-open', hayModalVisible);
    }

    function mostrar(modal) {
        if (!modal) return;
        modal.hidden = false;
        sincronizarBloqueoPagina();
        const primerControl = modal.querySelector('button, input, select, textarea');
        if (primerControl) primerControl.focus();
    }

    function ocultar(modal) {
        if (!modal) return;
        modal.hidden = true;
        sincronizarBloqueoPagina();
        botonAbrir.focus();
    }

    function cancelarConsultaDisponibilidad() {
        if (solicitudDisponibilidad) {
            solicitudDisponibilidad.abort();
            solicitudDisponibilidad = null;
        }
    }

    function restaurarOpciones(valorSeleccionado = horaInicial) {
        Array.from(hora.options).forEach((opcion) => {
            if (!opcion.dataset.horaBase) return;
            opcion.disabled = false;
            opcion.textContent = opcion.dataset.horaBase;
        });
        hora.value = valorSeleccionado;
    }

    function restablecerFormulario() {
        cancelarConsultaDisponibilidad();
        formulario.reset();
        fecha.value = fechaInicial;
        restaurarOpciones(horaInicial);
        hora.disabled = false;
        if (estado) estado.hidden = true;
        if (error) error.hidden = true;
        enviando = false;
        botonGuardar.disabled = false;
        botonGuardar.removeAttribute('aria-busy');
        if (textoGuardar) textoGuardar.textContent = textoGuardarInicial;
    }

    async function actualizarDisponibilidad() {
        const fechaSeleccionada = fecha.value;
        const horaSeleccionada = hora.value;
        cancelarConsultaDisponibilidad();
        restaurarOpciones(horaSeleccionada);
        if (error) error.hidden = true;

        if (!fechaSeleccionada || !disponibilidadUrl) return;

        const controlador = new AbortController();
        solicitudDisponibilidad = controlador;
        if (estado) estado.hidden = false;
        hora.disabled = true;

        try {
            const url = new URL(disponibilidadUrl, window.location.origin);
            url.searchParams.set('fecha', fechaSeleccionada);
            if (citaId) url.searchParams.set('excluir_cita_id', citaId);

            const response = await fetch(url, {
                headers: { Accept: 'application/json' },
                cache: 'no-store',
                signal: controlador.signal
            });
            if (!response.ok) {
                throw new Error('No fue posible consultar la disponibilidad.');
            }

            const horasOcupadas = await response.json();
            if (!Array.isArray(horasOcupadas)) {
                throw new Error('La respuesta de disponibilidad no es válida.');
            }

            horasOcupadas.forEach((horaOcupada) => {
                const opcion = Array.from(hora.options).find(
                    (elemento) => elemento.value === horaOcupada
                );
                if (opcion) {
                    opcion.disabled = true;
                    opcion.textContent = `${opcion.dataset.horaBase} (Ocupada)`;
                }
            });

            if (hora.selectedOptions[0] && hora.selectedOptions[0].disabled) {
                hora.value = '';
            }
        } catch (excepcion) {
            if (excepcion.name !== 'AbortError' && error) {
                error.hidden = false;
            }
        } finally {
            if (solicitudDisponibilidad === controlador) {
                hora.disabled = false;
                if (estado) estado.hidden = true;
                solicitudDisponibilidad = null;
            }
        }
    }

    function abrirFormularioCita() {
        if (modalAdvertencia) ocultar(modalAdvertencia);
        mostrar(modalCita);
        actualizarDisponibilidad();
    }

    function cerrarFormularioCita() {
        ocultar(modalCita);
        restablecerFormulario();
    }

    botonAbrir.addEventListener('click', () => {
        if (tieneCita && modalAdvertencia) {
            mostrar(modalAdvertencia);
        } else {
            abrirFormularioCita();
        }
    });

    document.getElementById('btnConfirmarCambioCita')?.addEventListener('click', abrirFormularioCita);
    document.getElementById('btnCerrarAdvertenciaCita')?.addEventListener('click', () => ocultar(modalAdvertencia));
    document.getElementById('btnCancelarAdvertenciaCita')?.addEventListener('click', () => ocultar(modalAdvertencia));
    document.getElementById('btnCerrarModalCita')?.addEventListener('click', cerrarFormularioCita);
    document.getElementById('btnCancelarModalCita')?.addEventListener('click', cerrarFormularioCita);
    fecha.addEventListener('change', actualizarDisponibilidad);

    modalCita.addEventListener('click', (evento) => {
        if (evento.target === modalCita) cerrarFormularioCita();
    });
    if (modalAdvertencia) {
        modalAdvertencia.addEventListener('click', (evento) => {
            if (evento.target === modalAdvertencia) ocultar(modalAdvertencia);
        });
    }

    document.addEventListener('keydown', (evento) => {
        if (evento.key !== 'Escape') return;
        if (!modalCita.hidden) cerrarFormularioCita();
        else if (modalAdvertencia && !modalAdvertencia.hidden) ocultar(modalAdvertencia);
    });

    formulario.addEventListener('submit', (evento) => {
        if (enviando) {
            evento.preventDefault();
            return;
        }
        enviando = true;
        botonGuardar.disabled = true;
        botonGuardar.setAttribute('aria-busy', 'true');
        if (textoGuardar) textoGuardar.textContent = 'Guardando…';
    });

    window.addEventListener('pageshow', () => {
        modales.forEach((modal) => { modal.hidden = true; });
        restablecerFormulario();
        sincronizarBloqueoPagina();
    });
    window.addEventListener('pagehide', cancelarConsultaDisponibilidad);

    modales.forEach((modal) => { modal.hidden = true; });
    restablecerFormulario();
    sincronizarBloqueoPagina();
}



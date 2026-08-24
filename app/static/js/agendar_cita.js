/** Flujo local, accesible y sin dependencias para agendar desde el KPI. */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-appointment-scheduler]').forEach(initializeAppointmentScheduler);
});

function initializeAppointmentScheduler(container) {
    const form = container.querySelector('[data-appointment-form]');
    const patientFinder = container.querySelector('.appointment-patient-finder');
    const patientSearch = container.querySelector('[data-patient-search]');
    const patientList = container.querySelector('[data-patient-list]');
    const patientId = container.querySelector('[data-patient-id]');
    const patientResults = container.querySelector('[data-patient-results]');
    const selectedPatientCard = container.querySelector('[data-selected-patient]');
    const selectedPatientName = container.querySelector('[data-selected-patient-name]');
    const selectedPatientRecord = container.querySelector('[data-selected-patient-record]');
    const selectedPatientPhone = container.querySelector('[data-selected-patient-phone]');
    const clearPatientButton = container.querySelector('[data-clear-patient]');
    const selectedDate = container.querySelector('[data-selected-date]');
    const selectedTime = container.querySelector('[data-selected-time]');
    const customDate = container.querySelector('[data-custom-date]');
    const calendarButtons = Array.from(container.querySelectorAll('[data-calendar-date]'));
    const timeGrid = container.querySelector('[data-time-grid]');
    const availabilityStatus = container.querySelector('[data-availability-status]');
    const submitButton = container.querySelector('[data-appointment-submit]');
    const summaryPatient = container.querySelector('[data-summary-patient]');
    const summaryRecord = container.querySelector('[data-summary-record]');
    const summaryDate = container.querySelector('[data-summary-date]');
    const summaryTime = container.querySelector('[data-summary-time]');
    const existingWarning = container.querySelector('[data-existing-warning]');
    const existingCopy = container.querySelector('[data-existing-copy]');
    const existingLink = container.querySelector('[data-existing-link]');
    const reason = container.querySelector('[name="motivo"]');
    const characterCount = container.querySelector('[data-character-count]');
    const availabilityUrl = container.dataset.availabilityUrl;
    const patientSearchUrl = container.dataset.patientSearchUrl;

    if (!form || !patientId || !selectedDate || !selectedTime || !timeGrid || !availabilityStatus || !submitButton) return;

    let availabilityRequest = null;
    let patientSearchRequest = null;
    let patientSearchTimer = null;
    let patientMatches = [];
    let activePatientIndex = -1;
    let availabilityReady = false;
    let submitting = false;
    const initialTime = selectedTime.value;
    let selectedPatient = patientId.value && selectedPatientCard ? {
        id: patientId.value,
        name: selectedPatientCard.dataset.patientName || '',
        record: selectedPatientCard.dataset.patientRecord || '—',
        phone: selectedPatientCard.dataset.patientPhone || '',
        detailUrl: selectedPatientCard.dataset.patientDetailUrl || '#',
        existingAppointment: selectedPatientCard.dataset.existingAppointment || '',
    } : null;

    function hidePatientResults() {
        if (patientList) {
            patientList.hidden = true;
            patientList.replaceChildren();
        }
        if (patientSearch) {
            patientSearch.setAttribute('aria-expanded', 'false');
            patientSearch.removeAttribute('aria-activedescendant');
        }
        patientMatches = [];
        activePatientIndex = -1;
    }

    function updatePatientSummary() {
        const hasExistingAppointment = Boolean(selectedPatient?.existingAppointment);
        if (summaryPatient) summaryPatient.textContent = selectedPatient?.name || 'Selecciona un paciente';
        if (summaryRecord) summaryRecord.textContent = selectedPatient?.record || '—';
        if (existingWarning) existingWarning.hidden = !hasExistingAppointment;
        if (existingCopy) existingCopy.textContent = selectedPatient?.existingAppointment || '';
        if (existingLink) existingLink.href = selectedPatient?.detailUrl || '#';
        updateSubmitState();
    }

    function renderSelectedPatient() {
        if (selectedPatientCard) selectedPatientCard.hidden = !selectedPatient;
        if (selectedPatientName) selectedPatientName.textContent = selectedPatient?.name || '';
        if (selectedPatientRecord) selectedPatientRecord.textContent = selectedPatient?.record || '';
        if (selectedPatientPhone) selectedPatientPhone.textContent = selectedPatient?.phone || '';
        patientId.value = selectedPatient?.id || '';
        updatePatientSummary();
    }

    function selectPatient(record) {
        selectedPatient = record;
        if (patientSearch) patientSearch.value = record.name;
        if (patientResults) patientResults.textContent = 'Paciente seleccionado.';
        hidePatientResults();
        renderSelectedPatient();
    }

    function setActivePatient(index) {
        if (!patientList || !patientMatches.length) return;
        activePatientIndex = (index + patientMatches.length) % patientMatches.length;
        patientList.querySelectorAll('[role="option"]').forEach((option, optionIndex) => {
            const active = optionIndex === activePatientIndex;
            option.classList.toggle('is-active', active);
            option.setAttribute('aria-selected', String(active));
            if (active) {
                patientSearch?.setAttribute('aria-activedescendant', option.id);
                option.scrollIntoView({ block: 'nearest' });
            }
        });
    }

    function renderPatientResults(records) {
        if (!patientList || !patientSearch) return;
        patientList.replaceChildren();
        patientMatches = records;
        activePatientIndex = -1;
        if (!records.length) {
            patientList.hidden = true;
            patientSearch.setAttribute('aria-expanded', 'false');
            if (patientResults) patientResults.textContent = 'No se encontraron pacientes activos con esos datos.';
            return;
        }

        records.forEach((record, index) => {
            const option = document.createElement('button');
            option.type = 'button';
            option.id = `appointment-patient-result-${record.id}`;
            option.className = 'appointment-search-result';
            option.setAttribute('role', 'option');
            option.setAttribute('aria-selected', 'false');

            const identity = document.createElement('span');
            identity.className = 'appointment-search-result-copy';
            const name = document.createElement('strong');
            name.textContent = record.name;
            const detail = document.createElement('small');
            detail.textContent = `${record.record} · ${record.phone}`;
            identity.append(name, detail);
            option.appendChild(identity);

            if (record.existingAppointment) {
                const badge = document.createElement('span');
                badge.className = 'appointment-search-result-badge';
                badge.textContent = 'Cita programada';
                option.appendChild(badge);
            }
            option.addEventListener('pointermove', () => setActivePatient(index));
            option.addEventListener('click', () => selectPatient(record));
            patientList.appendChild(option);
        });
        patientList.hidden = false;
        patientSearch.setAttribute('aria-expanded', 'true');
        if (patientResults) {
            patientResults.textContent = `${records.length} ${records.length === 1 ? 'paciente encontrado' : 'pacientes encontrados'}. Selecciona uno para continuar.`;
        }
    }

    async function searchPatients(query) {
        if (!patientSearchUrl) return;
        if (patientSearchRequest) patientSearchRequest.abort();
        const controller = new AbortController();
        patientSearchRequest = controller;
        if (patientResults) patientResults.textContent = 'Buscando paciente…';
        patientSearch?.setAttribute('aria-busy', 'true');
        try {
            const url = new URL(patientSearchUrl, window.location.origin);
            url.searchParams.set('busqueda', query);
            const response = await fetch(url, {
                headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                cache: 'no-store',
                signal: controller.signal,
            });
            const data = await response.json();
            if (!response.ok || !data.success || !Array.isArray(data.resultados)) {
                throw new Error(data.error || 'No fue posible buscar pacientes.');
            }
            const records = data.resultados.map((item) => ({
                id: String(item.id),
                name: item.nombre,
                record: item.expediente,
                phone: item.telefono,
                detailUrl: item.detalle_url,
                existingAppointment: item.cita_programada?.etiqueta || '',
            }));
            renderPatientResults(records);
        } catch (error) {
            if (error.name === 'AbortError') return;
            hidePatientResults();
            if (patientResults) patientResults.textContent = error.message || 'No fue posible buscar pacientes.';
        } finally {
            if (patientSearchRequest === controller) {
                patientSearchRequest = null;
                patientSearch?.removeAttribute('aria-busy');
            }
        }
    }

    function schedulePatientSearch() {
        if (patientSearchTimer) window.clearTimeout(patientSearchTimer);
        if (patientSearchRequest) patientSearchRequest.abort();
        const query = String(patientSearch?.value || '').trim();
        if (selectedPatient && query !== selectedPatient.name) {
            selectedPatient = null;
            renderSelectedPatient();
        }
        if (query.length < 2) {
            hidePatientResults();
            if (patientResults) patientResults.textContent = 'Escribe al menos 2 caracteres para buscar.';
            return;
        }
        patientSearchTimer = window.setTimeout(() => {
            patientSearchTimer = null;
            searchPatients(query);
        }, 250);
    }

    function updateDateSummary() {
        if (!summaryDate) return;
        const [year, month, day] = String(selectedDate.value || '').split('-').map(Number);
        if (!year || !month || !day) {
            summaryDate.textContent = '—';
            return;
        }
        summaryDate.textContent = new Intl.DateTimeFormat('es-MX', {
            weekday: 'short', day: '2-digit', month: 'long', year: 'numeric', timeZone: 'UTC',
        }).format(new Date(Date.UTC(year, month - 1, day)));
    }

    function updateTimeSummary() {
        if (summaryTime) summaryTime.textContent = selectedTime.value || '—';
    }

    function updateSubmitState() {
        const patientReady = Boolean(patientId.value) && !selectedPatient?.existingAppointment;
        submitButton.disabled = !(patientReady && selectedDate.value && selectedTime.value && availabilityReady) || submitting;
    }

    function selectDate(dateValue) {
        if (!dateValue) return;
        selectedDate.value = dateValue;
        if (customDate) customDate.value = dateValue;
        calendarButtons.forEach((button) => {
            const active = button.dataset.calendarDate === dateValue;
            button.classList.toggle('is-selected', active);
            button.setAttribute('aria-pressed', String(active));
        });
        updateDateSummary();
        loadAvailability(dateValue);
    }

    function renderTimes(slots) {
        timeGrid.replaceChildren();
        const previousTime = selectedTime.value || initialTime;
        let previousStillAvailable = false;
        slots.forEach((slot) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'appointment-time';
            button.textContent = slot.hora;
            button.dataset.appointmentTime = slot.hora;
            button.disabled = !slot.disponible;
            button.setAttribute('aria-pressed', 'false');
            if (!slot.disponible) {
                const stateLabel = slot.estado === 'ocupado' ? 'ocupado' : 'transcurrido';
                button.setAttribute('aria-label', `${slot.hora}, ${stateLabel}`);
                button.title = stateLabel === 'ocupado' ? 'Horario ocupado' : 'Horario transcurrido';
            } else {
                button.setAttribute('aria-label', `${slot.hora}, disponible`);
                button.addEventListener('click', () => {
                    timeGrid.querySelectorAll('[data-appointment-time]').forEach((item) => {
                        const active = item === button;
                        item.classList.toggle('is-selected', active);
                        item.setAttribute('aria-pressed', String(active));
                    });
                    selectedTime.value = slot.hora;
                    updateTimeSummary();
                    updateSubmitState();
                });
                if (slot.hora === previousTime) {
                    button.classList.add('is-selected');
                    button.setAttribute('aria-pressed', 'true');
                    previousStillAvailable = true;
                }
            }
            timeGrid.appendChild(button);
        });
        selectedTime.value = previousStillAvailable ? previousTime : '';
        updateTimeSummary();
    }

    async function loadAvailability(dateValue) {
        if (availabilityRequest) availabilityRequest.abort();
        availabilityReady = false;
        selectedTime.value = '';
        timeGrid.replaceChildren();
        availabilityStatus.hidden = false;
        availabilityStatus.classList.remove('is-error');
        const loadingIcon = document.createElement('i');
        loadingIcon.className = 'fas fa-circle-notch fa-spin';
        loadingIcon.setAttribute('aria-hidden', 'true');
        availabilityStatus.replaceChildren(loadingIcon, document.createTextNode(' Consultando disponibilidad…'));
        updateTimeSummary();
        updateSubmitState();

        const controller = new AbortController();
        availabilityRequest = controller;
        try {
            const url = new URL(availabilityUrl, window.location.origin);
            url.searchParams.set('fecha', dateValue);
            const response = await fetch(url, {
                headers: { Accept: 'application/json' },
                cache: 'no-store',
                signal: controller.signal,
            });
            const data = await response.json();
            if (!response.ok || !data.success || !Array.isArray(data.horarios)) {
                throw new Error(data.error || 'No fue posible consultar la disponibilidad.');
            }
            renderTimes(data.horarios);
            const availableCount = data.horarios.filter((slot) => slot.disponible).length;
            availabilityStatus.textContent = availableCount
                ? `${availableCount} ${availableCount === 1 ? 'horario disponible' : 'horarios disponibles'} para esta fecha.`
                : 'No hay horarios disponibles para esta fecha.';
            availabilityReady = true;
        } catch (error) {
            if (error.name === 'AbortError') return;
            availabilityStatus.classList.add('is-error');
            availabilityStatus.textContent = error.message || 'No fue posible consultar la disponibilidad.';
        } finally {
            if (availabilityRequest === controller) availabilityRequest = null;
            updateSubmitState();
        }
    }

    patientSearch?.addEventListener('input', schedulePatientSearch);
    patientSearch?.addEventListener('keydown', (event) => {
        if (patientList?.hidden || !patientMatches.length) return;
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            setActivePatient(activePatientIndex + 1);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            setActivePatient(activePatientIndex - 1);
        } else if (event.key === 'Enter' && activePatientIndex >= 0) {
            event.preventDefault();
            selectPatient(patientMatches[activePatientIndex]);
        } else if (event.key === 'Escape') {
            event.preventDefault();
            hidePatientResults();
        }
    });
    clearPatientButton?.addEventListener('click', () => {
        selectedPatient = null;
        if (patientSearch) patientSearch.value = '';
        if (patientResults) patientResults.textContent = 'Escribe al menos 2 caracteres para buscar.';
        hidePatientResults();
        renderSelectedPatient();
        patientSearch?.focus();
    });
    document.addEventListener('pointerdown', (event) => {
        if (patientFinder && !patientFinder.contains(event.target)) hidePatientResults();
    });
    calendarButtons.forEach((button) => button.addEventListener('click', () => selectDate(button.dataset.calendarDate)));
    customDate?.addEventListener('change', () => selectDate(customDate.value));
    reason?.addEventListener('input', () => {
        if (characterCount) characterCount.textContent = `${reason.value.length} / 500`;
    });
    form.addEventListener('submit', (event) => {
        updateSubmitState();
        if (submitButton.disabled || submitting) {
            event.preventDefault();
            return;
        }
        submitting = true;
        submitButton.disabled = true;
        submitButton.setAttribute('aria-busy', 'true');
        const label = submitButton.querySelector('span');
        if (label) label.textContent = 'Agendando…';
    });
    window.addEventListener('pagehide', () => {
        availabilityRequest?.abort();
        patientSearchRequest?.abort();
        if (patientSearchTimer) window.clearTimeout(patientSearchTimer);
    });

    if (reason && characterCount) characterCount.textContent = `${reason.value.length} / 500`;
    renderSelectedPatient();
    if (selectedPatient && patientResults) patientResults.textContent = 'Paciente seleccionado.';
    updateDateSummary();
    updateTimeSummary();
    selectDate(selectedDate.value);
}

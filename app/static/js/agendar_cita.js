/** Flujo local, accesible y sin dependencias para agendar desde el KPI. */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-appointment-scheduler]').forEach(initializeAppointmentScheduler);
});

function initializeAppointmentScheduler(container) {
    const form = container.querySelector('[data-appointment-form]');
    const patientSearch = container.querySelector('[data-patient-search]');
    const patientSelect = container.querySelector('[data-patient-select]');
    const patientResults = container.querySelector('[data-patient-results]');
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

    if (!form || !selectedDate || !selectedTime || !timeGrid || !availabilityStatus || !submitButton) return;

    let availabilityRequest = null;
    let availabilityReady = false;
    let submitting = false;
    const initialTime = selectedTime.value;
    const patientRecords = patientSelect
        ? Array.from(patientSelect.options).filter((option) => option.value).map((option) => ({
            value: option.value,
            label: option.textContent,
            search: option.dataset.search || option.textContent.toLocaleLowerCase('es-MX'),
            name: option.dataset.name || option.textContent,
            record: option.dataset.record || '—',
            phone: option.dataset.phone || '',
            detailUrl: option.dataset.detailUrl || '#',
            existingAppointment: option.dataset.existingAppointment || '',
            selected: option.selected,
        }))
        : [];

    function selectedPatientOption() {
        return patientSelect?.selectedOptions?.[0] || null;
    }

    function updatePatientSummary() {
        const option = selectedPatientOption();
        const hasExistingAppointment = Boolean(option?.dataset.existingAppointment);
        if (summaryPatient) summaryPatient.textContent = option?.dataset.name || 'Selecciona un paciente';
        if (summaryRecord) summaryRecord.textContent = option?.dataset.record || '—';
        if (existingWarning) existingWarning.hidden = !hasExistingAppointment;
        if (existingCopy) existingCopy.textContent = hasExistingAppointment ? option.dataset.existingAppointment : '';
        if (existingLink && option) existingLink.href = option.dataset.detailUrl || '#';
        updateSubmitState();
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
        const option = selectedPatientOption();
        const patientReady = Boolean(option?.value) && !option?.dataset.existingAppointment;
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

    function filterPatients() {
        if (!patientSelect) return;
        const query = String(patientSearch?.value || '').trim().toLocaleLowerCase('es-MX');
        const previousValue = patientSelect.value;
        const matches = patientRecords.filter((record) => !query || record.search.includes(query));
        patientSelect.replaceChildren();
        const placeholder = new Option('Selecciona un paciente registrado', '', false, !matches.some((record) => record.value === previousValue));
        placeholder.disabled = true;
        patientSelect.appendChild(placeholder);
        matches.forEach((record) => {
            const option = new Option(record.label, record.value, false, record.value === previousValue);
            option.dataset.search = record.search;
            option.dataset.name = record.name;
            option.dataset.record = record.record;
            option.dataset.phone = record.phone;
            option.dataset.detailUrl = record.detailUrl;
            if (record.existingAppointment) option.dataset.existingAppointment = record.existingAppointment;
            patientSelect.appendChild(option);
        });
        if (patientResults) {
            patientResults.textContent = `${matches.length} ${matches.length === 1 ? 'paciente encontrado' : 'pacientes encontrados'}`;
        }
        updatePatientSummary();
    }

    patientSearch?.addEventListener('input', filterPatients);
    patientSelect?.addEventListener('change', updatePatientSummary);
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
    window.addEventListener('pagehide', () => availabilityRequest?.abort());

    if (reason && characterCount) characterCount.textContent = `${reason.value.length} / 500`;
    updatePatientSummary();
    updateDateSummary();
    updateTimeSummary();
    selectDate(selectedDate.value);
}

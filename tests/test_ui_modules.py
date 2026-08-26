from datetime import date, datetime, time, timedelta
from pathlib import Path

from app import db_orm as db
from app.models.cita import Cita
from app.models.historial_clinico import HistorialClinico
from app.models.paciente import Paciente
from app.models.plantilla import PlantillaMensaje
from app.models.valoracion_antropometrica import ValoracionAntropometrica


def _patient(name="Marina", phone="5512345678"):
    patient = Paciente(
        nombre=name,
        apellido_paterno="García",
        apellido_materno="López",
        genero="mujer",
        fecha_nacimiento=date(1990, 5, 10),
        telefono=phone,
        correo=f"{name.lower()}@example.test",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.commit()
    return patient


def _assessment(patient_id):
    assessment = ValoracionAntropometrica(
        paciente_id=patient_id,
        numero_cita=1,
        fecha=date.today(),
        motivo_consulta="Revisión de seguimiento",
        sintomas="Cefalea ocasional",
        impresion_diagnostica="Cefalea en estudio",
        plan_tratamiento="Vigilancia y control",
        prescripcion="Hidratación y reposo",
        tension_arterial="120/80",
        frecuencia_cardiaca=72,
        frecuencia_respiratoria=16,
        temperatura=36.5,
        saturacion_oxigeno=98,
        estatura=170,
        peso=70,
        imc=24.2,
    )
    db.session.add(assessment)
    db.session.commit()
    return assessment


def test_history_list_uses_current_model_fields(app, client, login):
    login()
    with app.app_context():
        patient = _patient()
        db.session.add(
            HistorialClinico(
                paciente_id=patient.id,
                enfermedades_previas="Asma controlada",
                alergias_medicamentosas="Penicilina",
                medicamentos_actuales="Ninguno",
                actividad_fisica="Caminata tres veces por semana",
            )
        )
        db.session.commit()

    response = client.get("/historial-clinico/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Marina García López" in page
    assert "Asma controlada" in page
    assert "Penicilina" in page
    assert "Caminata tres veces por semana" in page
    assert "tipo_actividad_fisica" not in page
    assert "Antecedentes y padecimientos" in page

    history_partial = (
        Path(__file__).parents[1] / "app" / "templates" / "pacientes" / "partials" / "_historial_clinico.html"
    ).read_text(encoding="utf-8")
    assert history_partial.index("Historial Médico") < history_partial.index("Alimentación")
    assert history_partial.index("Alimentación") < history_partial.index("Actividad Física")


def test_patient_history_and_consultation_empty_states(client, login):
    login()
    patients = client.get("/pacientes/activos").get_data(as_text=True)
    histories = client.get("/historial-clinico/").get_data(as_text=True)
    assessments = client.get("/valoraciones/").get_data(as_text=True)

    assert "No hay pacientes activos registrados" in patients
    assert "Registrar paciente" in patients
    assert "No hay historiales clínicos registrados" in histories
    assert "No hay consultas clínicas registradas" in assessments


def test_patient_search_accepts_phone_and_email(app):
    with app.app_context():
        patient = _patient(phone="5511112233")
        assert Paciente.buscar("111122")[0].id == patient.id
        assert Paciente.buscar("marina@example.test")[0].id == patient.id


def test_dashboard_kpis_match_persisted_records(app, client, login):
    login()
    with app.app_context():
        patient = _patient()
        db.session.add(HistorialClinico(paciente_id=patient.id, enfermedades_previas="Asma"))
        db.session.add(PlantillaMensaje(titulo="Seguimiento", contenido="Hola {nombre}", esta_activa=True))
        db.session.add(
            Cita(
                paciente_id=patient.id,
                fecha=date.today(),
                hora=time(9, 30),
                motivo="Consulta de seguimiento",
                estatus="Programada",
            )
        )
        db.session.commit()
        _assessment(patient.id)

    page = client.get("/").get_data(as_text=True)
    assert 'data-kpi="pacientes">1</strong>' in page
    assert 'data-kpi="citas-hoy">1</strong>' in page
    assert 'data-kpi="consultas-pendientes">1</strong>' in page
    assert 'data-kpi="ingresos"' not in page
    assert "Ingresos del mes" not in page
    assert "Agenda de hoy" in page
    assert "Citas y consultas" in page
    assert "Próximas citas" in page
    assert "Alertas clínicas y administrativas" not in page
    assert "Acciones rápidas" not in page
    assert "Pacientes recientes" in page
    assert "Pendientes de atención" in page
    assert page.count("Nuevo paciente") == 1
    assert page.count('class="dashboard-kpi-action"') == 3
    assert 'aria-label="Ver pacientes registrados"' in page
    assert 'aria-label="Ver agenda de hoy"' in page
    assert 'aria-label="Ver consultas clínicas"' in page
    assert "Sin citas programadas para hoy" not in page
    assert "Crear receta" not in page
    assert "Ver expedientes" not in page
    assert "Actividad reciente" in page
    assert "Acompañamiento Intermedio (14-15 Días)" in page
    assert page.index("Próximas citas") < page.index("Acompañamiento Intermedio (14-15 Días)") < page.index("Pacientes recientes")
    assert "Consulta de seguimiento" in page
    assert "EXP-0001" in page
    assert 'static/css/dashboard.css' in page
    assert 'class="fas fa-users"' in page
    assert 'class="fas fa-file-medical"' in page
    assert 'class="fas fa-clipboard-list"' in page
    assert "WhatsApp / SMS" not in page


def test_dashboard_pending_details_keep_readable_dark_theme_contrast():
    root = Path(__file__).parents[1]
    styles = (root / "app" / "static" / "css" / "dashboard.css").read_text(encoding="utf-8")

    def luminance(color):
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return (0.2126 * linear[0]) + (0.7152 * linear[1]) + (0.0722 * linear[2])

    def contrast(foreground, background):
        lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
        return (lighter + 0.05) / (darker + 0.05)

    assert 'html[data-theme="dark"] .dashboard-task-detail a {' in styles
    assert 'html[data-theme="dark"] .dashboard-task-detail a:focus-visible' in styles
    assert 'html[data-theme="dark"] .dashboard-task-detail a:hover small' in styles
    assert contrast("#d8ebea", "#10262d") >= 4.5
    assert contrast("#b9d2d3", "#10262d") >= 4.5
    assert contrast("#f0fdfa", "#173a42") >= 4.5
    assert contrast("#99f6e4", "#173a42") >= 4.5


def test_shell_navigation_theme_and_planned_modules_are_accessible(client, login):
    login()
    page = client.get("/").get_data(as_text=True)
    root = Path(__file__).parents[1]
    sidebar = (root / "app" / "templates" / "components" / "_sidebar.html").read_text(encoding="utf-8")
    app_script = (root / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    theme_init = (root / "app" / "static" / "js" / "theme-init.js").read_text(encoding="utf-8")
    shell_css = (root / "app" / "static" / "css" / "shell.css").read_text(encoding="utf-8")

    assert 'role="search"' in page
    assert 'name="busqueda"' in page
    assert "Consultorio principal" in page
    assert 'data-theme-toggle' in page
    assert 'aria-label="Abrir notificaciones"' in page
    assert 'aria-label="Ruta de navegación"' in page
    assert 'data-sidebar-toggle' in page
    assert "Agenda y citas" in sidebar
    assert "url_for('valoracion.todas_valoraciones', origen='recetas')" in sidebar
    assert 'data-planned-module="Recetas"' not in sidebar
    assert "Administración" in sidebar
    assert "Usuarios y permisos" in sidebar
    assert "Portal del paciente" in sidebar
    assert "Hospitalización" not in sidebar
    assert sidebar.count('data-planned-module=') >= 7
    assert 'aria-disabled="true"' in sidebar
    assert "sgpn-theme" in theme_init
    assert "localStorage.setItem('sgpn-theme'" in app_script
    assert "event.key === 'Escape'" in app_script
    assert "ArrowDown" in app_script
    assert ":focus-visible" in shell_css
    assert 'html[data-theme="dark"]' in shell_css
    assert "background: #061f26" in shell_css
    assert "background: #1d6c69" in shell_css
    assert ".shell-sidebar-account-panel" in shell_css
    assert ".shell-nav-group" in shell_css
    assert ".shell-nav-children" in shell_css
    assert "height: 100dvh" in shell_css
    assert "overflow: hidden" in shell_css
    assert "min-height: 3.65rem" in shell_css
    assert ".shell-main { min-height: 0" in shell_css
    assert "sameDocumentAnchor" in app_script
    assert "font-size: 0.82rem" in shell_css
    assert "font-size: 0.76rem" in shell_css
    assert '.hover\\:bg-gray-50:hover' in shell_css
    assert '.hover\\:bg-teal-100:hover' in shell_css
    assert "background-color: #112f36 !important" in shell_css
    assert "background-color: #134e4a !important" in shell_css


def test_recipe_sidebar_context_and_dashboard_layout(client, login):
    login()
    page = client.get("/").get_data(as_text=True)
    recipe_context = client.get("/valoraciones/?origen=recetas").get_data(as_text=True)
    dashboard_css = (Path(__file__).parents[1] / "app" / "static" / "css" / "dashboard.css").read_text(
        encoding="utf-8"
    )

    assert 'href="/valoraciones/?origen=recetas"' in page
    assert "Selecciona una consulta para gestionar sus recetas" in recipe_context
    assert 'aria-current="page"' in recipe_context
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in dashboard_css
    assert 'html[data-theme="dark"] .dashboard-panel-header' in dashboard_css
    assert "border-color: #29464d" in dashboard_css


def test_upcoming_appointments_are_ordered_and_visible(app, client, login):
    login()
    with app.app_context():
        patient = _patient(name="Lucía")
        tomorrow = datetime.now().date() + timedelta(days=1)
        later = Cita(paciente_id=patient.id, fecha=tomorrow, hora=time(13, 0), motivo="Control posterior", estatus="Programada")
        earlier = Cita(paciente_id=patient.id, fecha=tomorrow, hora=time(9, 0), motivo="Primera cita futura", estatus="Programada")
        db.session.add_all([later, earlier])
        db.session.commit()
        upcoming = Cita.obtener_proximas(5)
        assert [item.hora for item in upcoming[:2]] == [time(9, 0), time(13, 0)]

    page = client.get("/").get_data(as_text=True)
    assert "Primera cita futura" in page
    assert "Control posterior" in page


def test_consultation_tabs_use_local_navigation(app, client, login):
    login()
    with app.app_context():
        patient_id = _patient().id

    page = client.get(f"/valoraciones/paciente/{patient_id}/nueva").get_data(as_text=True)
    root = Path(__file__).parents[1]
    script = (root / "app" / "static" / "js" / "tabs.js").read_text(encoding="utf-8")
    shell_css = (root / "app" / "static" / "css" / "shell.css").read_text(encoding="utf-8")

    assert 'id="formValoracion"' in page
    assert "data-tabs" in page
    assert page.count('role="tab"') == 4
    assert 'data-tab-target="vitales"' in page
    assert 'data-tab-panel="vitales" class="space-y-5" hidden' in page
    assert 'class="clinical-tablist ' in page
    assert page.count('class="clinical-tab ') == 4
    assert 'class="clinical-form-footer ' in page
    assert 'class="clinical-button-secondary ' in page
    assert "activeTab" not in page
    assert '/static/js/tabs.js' in page
    assert "ArrowRight" in script
    assert "panel.hidden = !activo" in script
    assert "formulario.addEventListener('invalid'" in script
    assert 'html[data-theme="dark"] .bg-gray-100' in shell_css
    assert 'html[data-theme="dark"] .clinical-tab[aria-selected="false"]' in shell_css
    assert 'html[data-theme="dark"] .clinical-tab[aria-selected="true"]' in shell_css
    assert "html[data-theme=\"dark\"] .clinical-form-footer" in shell_css
    assert "border-color: #29464d" in shell_css


def test_dark_theme_uses_soft_surfaces_and_resets_native_controls():
    root = Path(__file__).parents[1]
    shell_css = (root / "app" / "static" / "css" / "shell.css").read_text(encoding="utf-8")

    assert "--shell-border: rgb(148 203 204 / 0.12)" in shell_css
    assert "[data-remove-medicine] { border: 0; background: transparent; }" in shell_css
    assert ".shell-nav-link {" in shell_css
    assert "background: transparent; color: #c5dadd; font: inherit" in shell_css
    assert 'html[data-theme="dark"] .bg-teal-50\\/30' in shell_css
    assert 'html[data-theme="dark"] .shell-main .medicine-row' in shell_css
    assert 'html[data-theme="dark"] .shell-main .bg-white.border' in shell_css
    assert ".prescription-replace-action" in shell_css
    assert 'html[data-theme="dark"] .prescription-replace-action' in shell_css
    assert ".protected-admin-field" in shell_css


def test_print_view_is_standalone_and_contains_clinical_note(app, client, login):
    anonymous = app.test_client()
    assert anonymous.get("/valoraciones/valoraciones/1/imprimir").status_code == 302

    login()
    with app.app_context():
        patient = _patient()
        assessment = _assessment(patient.id)
        assessment_id = assessment.id

    detail = client.get(f"/valoraciones/valoraciones/{assessment_id}").get_data(as_text=True)
    response = client.get(f"/valoraciones/valoraciones/{assessment_id}/imprimir")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f'/valoraciones/valoraciones/{assessment_id}/imprimir' in detail
    assert "onclick=\"window.print()\"" not in detail
    assert "Nota de consulta clínica" in page
    assert "Marina García López" in page
    assert "Revisión de seguimiento" in page
    assert "Cefalea ocasional" in page
    assert "120/80 mmHg" in page
    assert "Hidratación y reposo" in page
    assert "Guardar como PDF" in page
    assert "Encabezados y pies de página" in page
    assert "print-sheet" in page
    assert "@media print" in page
    assert "Cerrar Sesión" not in page
    assert "cdn.tailwindcss.com" not in page

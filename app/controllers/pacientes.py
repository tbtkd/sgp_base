import io
import re
import zipfile
from datetime import date, datetime, timedelta
from pathlib import PurePosixPath
from threading import Lock

import openpyxl
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import login_required
from app.core.security import roles_required
from app.core.validators import (
    ALLOWED_APPOINTMENT_STATUS,
    ValidationError,
    appointment_payload,
    assessment_payload,
    clean_text,
    date_value,
    enum_value,
    integer,
    number,
    patient_payload,
    payment_payload,
)
from app.models.cita import Cita
from app.models.historial_clinico import HistorialClinico
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.valoracion_antropometrica import ValoracionAntropometrica

pacientes = Blueprint("pacientes", __name__, url_prefix="/pacientes")
MAX_EXCEL_ROWS = 2000
MAX_XLSX_UNCOMPRESSED = 25 * 1024 * 1024
APPOINTMENT_CALENDAR_DAYS = 21
APPOINTMENT_MAX_FUTURE_DAYS = 730
WEEKDAYS_SHORT_ES = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
MONTHS_SHORT_ES = ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")
_APPOINTMENT_WRITE_LOCK = Lock()


def _flash_validation(error):
    flash(str(error), "error")


def _appointment_calendar(moment=None):
    current = moment or datetime.now()
    start = current.date()
    end = start + timedelta(days=APPOINTMENT_CALENDAR_DAYS - 1)
    occupied = {day: set() for day in (start + timedelta(days=offset) for offset in range(APPOINTMENT_CALENDAR_DAYS))}
    rows = (
        Cita.query.with_entities(Cita.fecha, Cita.hora)
        .filter(Cita.estatus == "Programada", Cita.fecha.between(start, end))
        .all()
    )
    for appointment_date, appointment_time in rows:
        occupied.setdefault(appointment_date, set()).add(appointment_time)

    days = []
    for offset in range(APPOINTMENT_CALENDAR_DAYS):
        target = start + timedelta(days=offset)
        available = sum(
            1
            for slot in Cita.HORARIOS_ATENCION
            if slot not in occupied.get(target, set()) and datetime.combine(target, slot) > current
        )
        days.append(
            {
                "fecha": target,
                "iso": target.isoformat(),
                "dia_semana": WEEKDAYS_SHORT_ES[target.weekday()],
                "mes": MONTHS_SHORT_ES[target.month - 1],
                "disponibles": available,
            }
        )
    return days


def _quick_appointment_context():
    calendar = _appointment_calendar()
    raw_date = request.form.get("proxima_cita_fecha") or request.args.get("fecha")
    selected_date = None
    if raw_date:
        try:
            candidate = date_value(raw_date, "Fecha de cita", allow_future=True)
            if date.today() <= candidate <= date.today() + timedelta(days=APPOINTMENT_MAX_FUTURE_DAYS):
                selected_date = candidate
        except ValidationError:
            selected_date = None
    if not selected_date:
        first_available = next((item for item in calendar if item["disponibles"]), calendar[0])
        selected_date = first_available["fecha"]
    patients = Paciente.buscar("", status="activo", ordenar_por="nombre", orden="asc")
    patient_ids = [patient.id for patient in patients]
    pending_by_patient = {}
    if patient_ids:
        pending_appointments = (
            Cita.query.filter(Cita.paciente_id.in_(patient_ids), Cita.estatus == "Programada")
            .order_by(Cita.fecha.asc(), Cita.hora.asc(), Cita.id.asc())
            .all()
        )
        for appointment in pending_appointments:
            pending_by_patient.setdefault(appointment.paciente_id, appointment)
    selected_patient = request.form.get("paciente_id") or request.args.get("paciente_id", "")
    return {
        "pacientes": patients,
        "citas_pendientes_por_paciente": pending_by_patient,
        "calendario_citas": calendar,
        "fecha_seleccionada": selected_date,
        "paciente_seleccionado": str(selected_patient or ""),
        "fecha_minima": date.today(),
        "fecha_maxima": date.today() + timedelta(days=APPOINTMENT_MAX_FUTURE_DAYS),
    }


@pacientes.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_paciente():
    if request.method == "POST":
        try:
            data = patient_payload(request.form)
            patient = Paciente.crear(**data, status="activo")
            db.session.flush()
            AuditLog.record("paciente.create", entity_type="paciente", entity_id=patient.id)
            db.session.commit()
            flash("Paciente registrado exitosamente.", "success")
            return redirect(url_for("pacientes.lista_pacientes_activos"))
        except ValidationError as error:
            _flash_validation(error)
        except IntegrityError:
            db.session.rollback()
            flash("No fue posible registrar al paciente por un dato duplicado.", "error")
    return render_template("pacientes/nuevo_paciente.html")


def _patient_list(status):
    search = str(request.args.get("busqueda", ""))[:100]
    order_by = request.args.get("ordenar_por", "id")
    order = request.args.get("orden", "desc")
    if order_by not in {"id", "nombre", "apellidos", "ultima_consulta"}:
        order_by = "id"
    if order not in {"asc", "desc"}:
        order = "desc"
    patients = Paciente.buscar(search, status=status, ordenar_por=order_by, orden=order)
    return render_template(
        "pacientes/lista_pacientes.html",
        pacientes=patients,
        busqueda=search,
        ordenar_por=order_by,
        orden=order,
        tipo_lista="activos" if status == "activo" else "inactivos",
    )


@pacientes.route("/activos")
@login_required
def lista_pacientes_activos():
    return _patient_list("activo")


@pacientes.route("/inactivos")
@login_required
def lista_pacientes_inactivos():
    return _patient_list("inactivo")


@pacientes.route("/<int:id>")
@login_required
def detalle_paciente(id):
    patient = db.session.get(Paciente, id)
    if not patient:
        flash("Paciente no encontrado.", "error")
        return redirect(url_for("pacientes.lista_pacientes_activos"))
    can_view_clinical = current_user.rol_clinico in {"admin", "medico"}
    assessments = ValoracionAntropometrica.obtener_por_paciente(id) if can_view_clinical else []
    current = assessments[0] if assessments else None
    previous = assessments[1] if len(assessments) > 1 else None
    differences = {}
    if current and previous:
        for field in [
            "cintura",
            "torax",
            "brazo",
            "bicep",
            "tricep",
            "cadera",
            "pierna",
            "pantorrilla",
            "subescapular",
            "suprailiaco",
            "femoral",
        ]:
            left, right = getattr(current, field), getattr(previous, field)
            if left is not None and right is not None:
                delta = left - right
                differences[field] = {
                    "valor": delta,
                    "tendencia": "aumento" if delta > 0 else "reduccion" if delta < 0 else "sin_cambio",
                }
    next_appointment = Cita.obtener_siguiente_cita(id)
    next_datetime = datetime.combine(next_appointment.fecha, next_appointment.hora) if next_appointment else None
    return render_template(
        "pacientes/detalle_paciente.html",
        paciente=patient,
        ultimo_pago=Pago.obtener_ultimo_pago(id),
        historial=HistorialClinico.obtener_por_paciente_id(id) if can_view_clinical else None,
        ultima_valoracion=current,
        valoracion_anterior=previous,
        diferencias=differences,
        siguiente_cita=next_datetime,
        cita_programada=next_appointment,
        today=datetime.now(),
    )


@pacientes.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_paciente(id):
    patient = db.session.get(Paciente, id)
    if not patient:
        flash("Paciente no encontrado.", "error")
        return redirect(url_for("pacientes.lista_pacientes_activos"))
    if request.method == "POST":
        try:
            data = patient_payload(request.form, include_status=True)
            for key, value in data.items():
                setattr(patient, key, value)
            AuditLog.record(
                "paciente.update", entity_type="paciente", entity_id=patient.id, metadata={"status": patient.status}
            )
            db.session.commit()
            flash("Paciente actualizado exitosamente.", "success")
            return redirect(url_for("pacientes.detalle_paciente", id=id))
        except ValidationError as error:
            _flash_validation(error)
    return render_template("pacientes/editar_paciente.html", paciente=patient)


@pacientes.route("/<int:id>/pago", methods=["POST"])
@login_required
def registrar_pago_paciente(id):
    patient = db.session.get(Paciente, id)
    if not patient:
        flash("Paciente no encontrado.", "error")
        return redirect(url_for("pacientes.lista_pacientes_activos"))
    try:
        data = payment_payload(request.form)
        payment = Pago(paciente_id=id, **data)
        db.session.add(payment)
        db.session.flush()
        AuditLog.record("pago.create", entity_type="pago", entity_id=payment.id, metadata={"paciente_id": id})
        db.session.commit()
        flash("Pago registrado exitosamente.", "success")
    except ValidationError as error:
        _flash_validation(error)
    return redirect(url_for("pacientes.detalle_paciente", id=id))


@pacientes.route("/<int:id>/cambiar-estado", methods=["POST"])
@login_required
def cambiar_estado(id):
    patient = db.session.get(Paciente, id)
    if not patient:
        return jsonify({"success": False, "error": "Paciente no encontrado"}), 404
    patient.status = "inactivo" if patient.status == "activo" else "activo"
    AuditLog.record(
        "paciente.status", entity_type="paciente", entity_id=patient.id, metadata={"status": patient.status}
    )
    db.session.commit()
    return jsonify({"success": True, "nuevo_estado": patient.status})


def _excel_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except (TypeError, ValueError):
            continue
    raise ValidationError("Formato de fecha inválido.")


def _extract_number(text, key):
    aliases = {
        "tc": "(?:tc|t)",
        "bc": "(?:bc|b)",
        "si": "(?:si|i)",
        "se": "(?:se|e)",
        "fem": "(?:fem|f)",
        "grasa": "grasa",
    }
    match = re.search(rf"{aliases[key]}\s*[:=]?\s*(\d+(?:[.,]\d+)?)", str(text or "").lower())
    return match.group(1) if match else None


def _validate_xlsx_archive(blob):
    stream = io.BytesIO(blob)
    if not zipfile.is_zipfile(stream):
        raise ValidationError("El archivo no tiene una estructura XLSX válida.")
    stream.seek(0)
    with zipfile.ZipFile(stream) as archive:
        members = archive.infolist()
        if len(members) > 500:
            raise ValidationError("El archivo contiene demasiados componentes internos.")
        total = 0
        for member in members:
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValidationError("El archivo contiene rutas internas no permitidas.")
            total += member.file_size
            if member.file_size > 10 * 1024 * 1024:
                raise ValidationError("El archivo contiene un componente interno demasiado grande.")
            if member.file_size and member.compress_size == 0:
                raise ValidationError("El archivo tiene una relación de compresión inválida.")
            if member.compress_size and member.file_size / member.compress_size > 100:
                raise ValidationError("El archivo tiene una relación de compresión no permitida.")
        if total > MAX_XLSX_UNCOMPRESSED:
            raise ValidationError("El contenido descomprimido excede el límite permitido.")


@pacientes.route("/<int:id>/cargar-excel", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def cargar_excel(id):
    if not db.session.get(Paciente, id):
        return jsonify({"success": False, "message": "Paciente no encontrado"}), 404
    if not current_user.puede_capturar_antropometria:
        return jsonify(
            {
                "success": False,
                "message": "La importación antropométrica sólo está disponible para profesionales de Nutrición.",
            }
        ), 403
    uploaded = request.files.get("excel_file") or request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify({"success": False, "message": "Selecciona un archivo XLSX"}), 400
    if not uploaded.filename.lower().endswith(".xlsx"):
        return jsonify({"success": False, "message": "Solo se permiten archivos .xlsx"}), 400
    blob = uploaded.read(5 * 1024 * 1024 + 1)
    if len(blob) > 5 * 1024 * 1024:
        return jsonify({"success": False, "message": "El archivo excede el límite de 5 MB"}), 413
    try:
        _validate_xlsx_archive(blob)
        workbook = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True, keep_links=False)
        sheet = workbook.active
        if sheet.max_row > MAX_EXCEL_ROWS or sheet.max_column > 100:
            raise ValidationError(f"La hoja excede el máximo de {MAX_EXCEL_ROWS} filas o 100 columnas.")
        height_raw = sheet["M8"].value
        height = number(height_raw, "Estatura", minimum=0.5, maximum=250)
        if height > 3:
            height = height / 100

        existing = {
            (row.numero_cita, row.fecha) for row in ValoracionAntropometrica.query.filter_by(paciente_id=id).all()
        }
        seen, pending, duplicates, errors = set(), [], 0, []
        for row_number in range(10, sheet.max_row + 1):
            visit_raw = sheet.cell(row=row_number, column=12).value
            date_raw = sheet.cell(row=row_number, column=13).value
            weight_raw = sheet.cell(row=row_number, column=14).value
            if visit_raw in (None, "") and date_raw in (None, "") and weight_raw in (None, ""):
                continue
            try:
                visit_number = number(visit_raw, "Número de cita", minimum=1, maximum=10000)
                if not visit_number.is_integer():
                    raise ValidationError("El número de cita debe ser entero.")
                visit_number = int(visit_number)
                assessment_date = _excel_date(date_raw)
                key = (visit_number, assessment_date)
                if key in existing or key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
                composite = sheet.cell(row=row_number, column=15).value
                folds = sheet.cell(row=row_number, column=22).value
                percent_raw = str(sheet.cell(row=row_number, column=23).value or "").replace("%", "")
                raw = {
                    "numero_cita": visit_number,
                    "fecha": assessment_date.strftime("%Y-%m-%d"),
                    "motivo_consulta": "Consulta importada desde expediente antropométrico",
                    "estatura": height,
                    "peso": weight_raw,
                    "grasa": _extract_number(composite, "grasa") or 0,
                    "cintura": sheet.cell(row=row_number, column=16).value,
                    "torax": sheet.cell(row=row_number, column=17).value,
                    "brazo": sheet.cell(row=row_number, column=18).value,
                    "cadera": sheet.cell(row=row_number, column=19).value,
                    "pierna": sheet.cell(row=row_number, column=20).value,
                    "pantorrilla": sheet.cell(row=row_number, column=21).value,
                    "tension_arterial": sheet.cell(row=row_number, column=24).value,
                    "frecuencia_cardiaca": sheet.cell(row=row_number, column=25).value,
                    "bicep": _extract_number(folds, "bc"),
                    "tricep": _extract_number(folds, "tc"),
                    "suprailiaco": _extract_number(folds, "si"),
                    "subescapular": _extract_number(folds, "se"),
                    "femoral": _extract_number(folds, "fem"),
                    "porcentaje_grasa": percent_raw,
                }
                pending.append(assessment_payload(raw, allow_anthropometry=True))
            except ValidationError as error:
                errors.append(f"Fila {row_number}: {error}")
        workbook.close()
        if errors:
            return jsonify(
                {
                    "success": False,
                    "message": "El archivo contiene datos inválidos; no se importó ningún registro.",
                    "errores": errors[:20],
                }
            ), 400
        for data in pending:
            ValoracionAntropometrica.crear(id, data, profesional=current_user)
        AuditLog.record(
            "valoracion.import",
            entity_type="paciente",
            entity_id=id,
            metadata={"created": len(pending), "duplicates": duplicates},
        )
        db.session.commit()
        return jsonify(
            {
                "success": True,
                "message": f"Se agregaron {len(pending)} registros; {duplicates} duplicados fueron omitidos.",
                "registros_duplicados": duplicates,
                "registros_procesados": len(pending),
                "errores": [],
            }
        )
    except (ValidationError, zipfile.BadZipFile, KeyError) as error:
        db.session.rollback()
        return jsonify({"success": False, "message": str(error)}), 400
    except (OSError, ValueError, TypeError):
        db.session.rollback()
        return jsonify({"success": False, "message": "No fue posible procesar el archivo XLSX."}), 400


def _appointment_values(form):
    data = appointment_payload(form)
    moment = datetime.combine(data["fecha"], data["hora"])
    if moment <= datetime.now():
        raise ValidationError("La cita debe programarse en una fecha y hora futuras.")
    return data


@pacientes.route("/agendar-cita", methods=["GET", "POST"])
@login_required
def agendar_cita_rapida():
    if request.method == "POST":
        try:
            patient_id = integer(request.form.get("paciente_id"), "Paciente", minimum=1)
            patient = db.session.get(Paciente, patient_id)
            if not patient or patient.status != "activo":
                raise ValidationError("Selecciona un paciente activo registrado.")
            data = _appointment_values(request.form)
            if data["fecha"] > date.today() + timedelta(days=APPOINTMENT_MAX_FUTURE_DAYS):
                raise ValidationError("La cita no puede programarse con más de dos años de anticipación.")

            with _APPOINTMENT_WRITE_LOCK:
                pending = Cita.obtener_cita_pendiente(patient.id)
                if pending:
                    raise ValidationError(
                        "El paciente ya tiene una cita programada. Modifícala desde el detalle del paciente."
                    )
                if not Cita.es_horario_disponible(data["fecha"], data["hora"]):
                    raise ValidationError("El horario seleccionado ya no está disponible.")
                appointment = Cita(
                    paciente_id=patient.id,
                    fecha=data["fecha"],
                    hora=data["hora"],
                    motivo=data["motivo"] or None,
                    estado="pendiente",
                    estatus="Programada",
                )
                db.session.add(appointment)
                db.session.flush()
                AuditLog.record(
                    "cita.create",
                    entity_type="cita",
                    entity_id=appointment.id,
                    metadata={"paciente_id": patient.id, "origen": "kpi_dashboard"},
                )
                db.session.commit()
            flash("Cita agendada exitosamente desde el Dashboard.", "success")
            return redirect(f"{url_for('main.index')}#agenda-hoy")
        except ValidationError as error:
            _flash_validation(error)
            return render_template("pacientes/agendar_cita.html", **_quick_appointment_context()), 400
    return render_template("pacientes/agendar_cita.html", **_quick_appointment_context())


@pacientes.route("/<int:id>/registrar_proxima_cita", methods=["POST"])
@login_required
def registrar_proxima_cita(id):
    patient = db.session.get(Paciente, id)
    if not patient:
        flash("Paciente no encontrado.", "error")
        return redirect(url_for("pacientes.lista_pacientes_activos"))
    try:
        data = _appointment_values(request.form)
        with _APPOINTMENT_WRITE_LOCK:
            appointment = Cita.obtener_cita_pendiente(id)
            if not Cita.es_horario_disponible(
                data["fecha"], data["hora"], appointment.id if appointment else None
            ):
                raise ValidationError("El horario seleccionado ya no está disponible.")
            action = "cita.update" if appointment else "cita.create"
            if not appointment:
                appointment = Cita(paciente_id=id)
                db.session.add(appointment)
            appointment.fecha, appointment.hora, appointment.motivo = (
                data["fecha"],
                data["hora"],
                data["motivo"] or None,
            )
            appointment.estado, appointment.estatus, appointment.motivo_cancelacion = (
                "pendiente",
                "Programada",
                None,
            )
            db.session.flush()
            AuditLog.record(action, entity_type="cita", entity_id=appointment.id, metadata={"paciente_id": id})
            db.session.commit()
        flash("Cita guardada exitosamente.", "success")
    except ValidationError as error:
        _flash_validation(error)
    return redirect(url_for("pacientes.detalle_paciente", id=id))


@pacientes.route("/<int:id>/actualizar_cita/<int:cita_id>", methods=["POST"])
@login_required
def actualizar_cita(id, cita_id):
    appointment = db.session.get(Cita, cita_id)
    if not appointment or appointment.paciente_id != id:
        flash("Cita no encontrada.", "error")
        return redirect(url_for("pacientes.detalle_paciente", id=id))
    try:
        data = _appointment_values(request.form)
        with _APPOINTMENT_WRITE_LOCK:
            if not Cita.es_horario_disponible(data["fecha"], data["hora"], appointment.id):
                raise ValidationError("El horario seleccionado ya no está disponible.")
            appointment.fecha, appointment.hora, appointment.motivo = (
                data["fecha"],
                data["hora"],
                data["motivo"] or None,
            )
            AuditLog.record("cita.update", entity_type="cita", entity_id=appointment.id)
            db.session.commit()
        flash("Cita actualizada exitosamente.", "success")
    except ValidationError as error:
        _flash_validation(error)
    return redirect(url_for("pacientes.detalle_paciente", id=id))


@pacientes.route("/disponibilidad_horas", methods=["GET"])
@login_required
def disponibilidad_horas():
    try:
        target = date_value(request.args.get("fecha"), "Fecha", allow_future=True)
    except ValidationError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    query = Cita.query.filter_by(fecha=target, estatus="Programada")
    exclude_appointment_id = request.args.get("excluir_cita_id", type=int)
    if exclude_appointment_id:
        query = query.filter(Cita.id != exclude_appointment_id)
    response = jsonify([item.hora.strftime("%H:%M") for item in query.order_by(Cita.hora).all()])
    response.headers["Cache-Control"] = "no-store"
    return response


@pacientes.route("/disponibilidad_citas", methods=["GET"])
@login_required
def disponibilidad_citas():
    try:
        target = date_value(request.args.get("fecha"), "Fecha", allow_future=True)
        if target < date.today():
            raise ValidationError("La fecha de cita no puede estar en el pasado.")
        if target > date.today() + timedelta(days=APPOINTMENT_MAX_FUTURE_DAYS):
            raise ValidationError("La disponibilidad sólo puede consultarse hasta dos años en el futuro.")
    except ValidationError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    response = jsonify(
        {
            "success": True,
            "fecha": target.isoformat(),
            "horarios": Cita.obtener_disponibilidad_dia(target),
        }
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@pacientes.route("/citas/<int:id>/cambiar-estatus", methods=["POST"])
@login_required
def cambiar_estatus_cita(id):
    appointment = db.session.get(Cita, id)
    if not appointment:
        return jsonify({"success": False, "error": "Cita no encontrada"}), 404
    try:
        payload = request.get_json(silent=True) or {}
        status = enum_value(payload.get("estatus"), "Estatus", ALLOWED_APPOINTMENT_STATUS)
        reason = clean_text(payload.get("motivo"), "Motivo", maximum=500)
        if status == "Cancelada" and not reason:
            raise ValidationError("Indica el motivo de cancelación.")
        appointment.estatus = status
        appointment.estado = "completada" if status == "Atendida" else "pendiente"
        appointment.motivo_cancelacion = reason if status in {"Cancelada", "No Asistió"} else None
        AuditLog.record("cita.status", entity_type="cita", entity_id=appointment.id, metadata={"status": status})
        db.session.commit()
        return jsonify({"success": True, "nuevo_estatus": status})
    except ValidationError as error:
        return jsonify({"success": False, "error": str(error)}), 400

import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import case, func, or_
from sqlalchemy.orm import joinedload

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import login_required
from app.core.security import roles_required
from app.core.text import search_key
from app.core.validators import (
    ALLOWED_PAYMENT_METHODS,
    ALLOWED_PAYMENT_STATUS,
    ValidationError,
    clean_text,
    date_value,
    enum_value,
    integer,
    payment_cancellation_payload,
)
from app.models.paciente import Paciente
from app.models.pago import Pago

pagos = Blueprint("pagos", __name__, url_prefix="/pagos")
MAX_PAYMENT_RANGE_DAYS = 366
PAYMENTS_PER_PAGE = 25
MAX_PAYMENT_EXPORT_ROWS = 10_000
REPORT_GROUPINGS = ("dia", "mes")


def _filters(args):
    today = date.today()
    start = date_value(args.get("desde") or today.isoformat(), "Fecha inicial", allow_future=True)
    end = date_value(args.get("hasta") or today.isoformat(), "Fecha final", allow_future=True)
    if end < start:
        raise ValidationError("La fecha final no puede ser anterior a la fecha inicial.")
    if end - start > timedelta(days=MAX_PAYMENT_RANGE_DAYS):
        raise ValidationError("El rango de pagos no puede exceder 366 días.")
    method = str(args.get("metodo") or "").strip()
    if method:
        method = enum_value(method, "Método de pago", ALLOWED_PAYMENT_METHODS)
    status = str(args.get("estatus") or "").strip()
    if status:
        status = enum_value(status, "Estatus", ALLOWED_PAYMENT_STATUS)
    grouping = enum_value(
        args.get("agrupacion") or "dia",
        "Agrupación",
        REPORT_GROUPINGS,
    )
    return {
        "q": clean_text(args.get("q"), "Búsqueda", maximum=100),
        "desde": start,
        "hasta": end,
        "metodo": method,
        "estatus": status,
        "agrupacion": grouping,
        "page": integer(args.get("page") or 1, "Página", minimum=1, maximum=100_000),
    }


def _payment_query(filters):
    query = Pago.query.join(Paciente)
    query = query.filter(Pago.fecha_pago.between(filters["desde"], filters["hasta"]))
    if filters["metodo"]:
        query = query.filter(Pago.metodo_pago == filters["metodo"])
    if filters["estatus"]:
        query = query.filter(Pago.estatus == filters["estatus"])
    normalized = search_key(filters["q"])
    if normalized:
        searchable_fields = (
            func.sgpn_search_key(Pago.folio),
            func.sgpn_search_key(Pago.concepto),
            func.sgpn_search_key(Paciente.nombre),
            func.sgpn_search_key(Paciente.apellido_paterno),
            func.sgpn_search_key(Paciente.apellido_materno),
        )
        # Cada palabra puede coincidir en una columna distinta. Esto permite
        # buscar un nombre completo aunque sus partes vivan en campos separados.
        for term in normalized.split():
            pattern = f"%{term}%"
            query = query.filter(or_(*(field.like(pattern) for field in searchable_fields)))
    return query


@pagos.route("/")
@login_required
@roles_required("admin", "recepcion")
def index():
    try:
        filters = _filters(request.args)
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("pagos.index"))

    query = _payment_query(filters)
    summary = query.with_entities(
        func.count(Pago.id),
        func.coalesce(func.sum(case((Pago.estatus == "vigente", Pago.monto_centavos), else_=0)), 0),
        func.coalesce(func.sum(case((Pago.estatus == "cancelado", 1), else_=0)), 0),
        func.coalesce(func.sum(case((Pago.estatus == "requiere_revision", 1), else_=0)), 0),
    ).one()
    breakdown = (
        query.with_entities(Pago.metodo_pago, func.coalesce(func.sum(Pago.monto_centavos), 0))
        .filter(Pago.estatus == "vigente")
        .group_by(Pago.metodo_pago)
        .order_by(Pago.metodo_pago.asc())
        .all()
    )
    report_series = []
    if current_user.rol_clinico == "admin":
        period_expression = (
            func.strftime("%Y-%m", Pago.fecha_pago)
            if filters["agrupacion"] == "mes"
            else func.strftime("%Y-%m-%d", Pago.fecha_pago)
        )
        report_series = (
            query.with_entities(
                period_expression.label("periodo"),
                func.count(Pago.id),
                func.coalesce(
                    func.sum(case((Pago.estatus == "vigente", Pago.monto_centavos), else_=0)),
                    0,
                ),
                func.coalesce(func.sum(case((Pago.estatus == "cancelado", 1), else_=0)), 0),
            )
            .group_by(period_expression)
            .order_by(period_expression.desc())
            .all()
        )
    pagination = (
        query.options(
            joinedload(Pago.paciente),
            joinedload(Pago.usuario_registro),
            joinedload(Pago.usuario_cancelacion),
            joinedload(Pago.cita),
        )
        .order_by(Pago.fecha_pago.desc(), Pago.created_at.desc(), Pago.id.desc())
        .paginate(page=filters["page"], per_page=PAYMENTS_PER_PAGE, error_out=False)
    )
    return render_template(
        "pagos/index.html",
        pagos=pagination.items,
        paginacion=pagination,
        filtros=filters,
        resumen={
            "movimientos": int(summary[0] or 0),
            "monto_centavos": int(summary[1] or 0),
            "cancelados": int(summary[2] or 0),
            "requieren_revision": int(summary[3] or 0),
        },
        desglose={method: int(cents or 0) for method, cents in breakdown},
        serie_reporte=[
            {
                "periodo": period,
                "movimientos": int(count or 0),
                "monto_centavos": int(cents or 0),
                "cancelados": int(cancelled or 0),
            }
            for period, count, cents, cancelled in report_series
        ],
        metodos=("efectivo", "tarjeta", "transferencia", "otro"),
        estatus_disponibles=("vigente", "cancelado", "requiere_revision"),
    )


def _csv_safe(value):
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def _payment_csv_response(payments, filename):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow(
        (
            "Folio",
            "Fecha",
            "Expediente",
            "Paciente",
            "Concepto",
            "Método",
            "Monto MXN",
            "Moneda",
            "Estado",
            "Registró",
            "Cita",
            "Fecha de cancelación",
            "Canceló",
            "Motivo de cancelación",
        )
    )
    for payment in payments:
        amount = Decimal(int(payment.monto_centavos or 0)) / Decimal(100)
        appointment = ""
        if payment.cita:
            appointment = f"{payment.cita.fecha.isoformat()} {payment.cita.hora.strftime('%H:%M')}"
        writer.writerow(
            tuple(
                _csv_safe(value)
                for value in (
                    payment.folio,
                    payment.fecha_pago.isoformat(),
                    f"EXP-{payment.paciente_id:04d}",
                    payment.paciente.nombre_completo,
                    payment.concepto,
                    payment.metodo_pago,
                    f"{amount:.2f}",
                    payment.moneda,
                    payment.estatus_etiqueta,
                    payment.usuario_registro.nombre_completo if payment.usuario_registro else "Registro migrado",
                    appointment,
                    payment.cancelado_at.isoformat(" ") if payment.cancelado_at else "",
                    payment.usuario_cancelacion.nombre_completo if payment.usuario_cancelacion else "",
                    payment.motivo_cancelacion or "",
                )
            )
        )
    response = Response("\ufeff" + stream.getvalue(), content_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store"
    return response


def _export_rows(query):
    if query.count() > MAX_PAYMENT_EXPORT_ROWS:
        raise ValidationError("La exportación excede 10,000 movimientos; reduce el rango o aplica filtros.")
    return (
        query.options(
            joinedload(Pago.paciente),
            joinedload(Pago.usuario_registro),
            joinedload(Pago.usuario_cancelacion),
            joinedload(Pago.cita),
        )
        .order_by(Pago.fecha_pago.desc(), Pago.created_at.desc(), Pago.id.desc())
        .all()
    )


@pagos.route("/exportar.csv")
@login_required
@roles_required("admin")
def exportar_csv():
    try:
        filters = _filters(request.args)
        payments = _export_rows(_payment_query(filters))
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("pagos.index"))
    AuditLog.record(
        "pago.export",
        entity_type="pago",
        metadata={
            "scope": "global",
            "desde": filters["desde"].isoformat(),
            "hasta": filters["hasta"].isoformat(),
            "rows": len(payments),
        },
    )
    db.session.commit()
    filename = f"pagos_{filters['desde'].isoformat()}_{filters['hasta'].isoformat()}.csv"
    return _payment_csv_response(payments, filename)


@pagos.route("/paciente/<int:paciente_id>/historial.csv")
@login_required
@roles_required("admin")
def exportar_paciente_csv(paciente_id):
    patient = db.session.get(Paciente, paciente_id)
    if not patient:
        abort(404)
    try:
        payments = _export_rows(Pago.query.filter(Pago.paciente_id == patient.id))
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("pacientes.detalle_paciente", id=patient.id))
    AuditLog.record(
        "pago.export",
        entity_type="paciente",
        entity_id=patient.id,
        metadata={"scope": "patient_history", "rows": len(payments)},
    )
    db.session.commit()
    filename = f"historial_pagos_EXP-{patient.id:04d}_{datetime.now():%Y%m%d}.csv"
    return _payment_csv_response(payments, filename)


def _safe_return_path(value):
    target = str(value or "")
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return url_for("pagos.index")
    if not (parsed.path.startswith("/pagos/") or parsed.path.startswith("/pacientes/")):
        return url_for("pagos.index")
    query = urlencode(parse_qsl(parsed.query, keep_blank_values=True))
    return urlunsplit(("", "", parsed.path, query, ""))


def _return_after_cancellation(value, payment):
    safe_target = _safe_return_path(value)
    parsed = urlsplit(safe_target)
    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    if parsed.path.startswith("/pagos/"):
        active_status = next((item_value for key, item_value in query_items if key == "estatus"), "")
        if active_status and active_status != "cancelado":
            query_items = [
                (key, item_value)
                for key, item_value in query_items
                if key not in {"q", "estatus", "page"}
            ]
            query_items.append(("q", payment.folio))
    return urlunsplit(("", "", parsed.path, urlencode(query_items), f"pago-{payment.id}"))


@pagos.route("/<int:pago_id>/cancelar", methods=["POST"])
@login_required
@roles_required("admin")
def cancelar(pago_id):
    payment = db.session.get(Pago, pago_id)
    if not payment:
        abort(404)
    return_to = _return_after_cancellation(request.form.get("return_to"), payment)
    if payment.estatus == "cancelado":
        AuditLog.record(
            "pago.cancel",
            entity_type="pago",
            entity_id=payment.id,
            outcome="denied",
            metadata={"paciente_id": payment.paciente_id, "reason": "already_cancelled"},
        )
        db.session.commit()
        flash(f"El pago {payment.folio} ya se encontraba cancelado.", "warning")
        return redirect(return_to)
    try:
        data = payment_cancellation_payload(request.form)
        previous_status = payment.cancelar(
            usuario_id=current_user.id,
            motivo=data["motivo_cancelacion"],
        )
        AuditLog.record(
            "pago.cancel",
            entity_type="pago",
            entity_id=payment.id,
            metadata={
                "paciente_id": payment.paciente_id,
                "folio": payment.folio,
                "estatus_anterior": previous_status,
            },
        )
        db.session.commit()
        flash(f"Pago {payment.folio} cancelado. El movimiento original permanece en el historial.", "success")
    except ValidationError as error:
        db.session.rollback()
        flash(str(error), "error")
    return redirect(return_to)

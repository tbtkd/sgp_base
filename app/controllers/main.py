from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app.models.paciente import Paciente
from app.models.valoracion_antropometrica import ValoracionAntropometrica
from app.models.cita import Cita
from app.models.bitacora import BitacoraContacto
from app.models.plantilla import PlantillaMensaje
from app import db_orm as db

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    """
    Renderiza la página principal del sistema con KPIs y actividad reciente.
    """
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    total_pacientes = Paciente.contar_activos()
    crecimiento_pacientes = Paciente.calcular_crecimiento_mensual()
    valoraciones_mes = ValoracionAntropometrica.contar_mes_vigente()
    
    # Cálculo dinámico del promedio diario
    dia_actual = datetime.now().day
    promedio_diario = round(valoraciones_mes / dia_actual, 1)
    
    pacientes_seguimiento = Paciente.contar_en_seguimiento()
    pacientes_sin_valoracion = Paciente.obtener_sin_valoracion_reciente(dias=30)
    
    citas_del_dia = Cita.obtener_citas_del_dia()
    
    pendientes_por_agendar = Paciente.obtener_pendientes_por_agendar()
    
    # Obtener valoraciones para seguimiento de 14-15 días
    seguimiento_14_15 = ValoracionAntropometrica.obtener_seguimiento_14_15_dias()

    # Si hay filtro de fechas, obtener actividad filtrada
    if fecha_inicio and fecha_fin:
        actividad_reciente = ValoracionAntropometrica.obtener_por_rango(fecha_inicio, fecha_fin)
    else:
        actividad_reciente = ValoracionAntropometrica.obtener_recientes(limite=10)
    
    plantilla_activa = PlantillaMensaje.obtener_activa()
    contenido_plantilla = plantilla_activa.contenido if plantilla_activa else "¡Hola, {nombre}! 👋 Te saluda la nutrióloga Aurora Ángeles. Han pasado {dias} días desde tu última consulta y quería saber cómo te has sentido con tu plan de alimentación y si te ha surgido alguna duda. ¡Sigo al pendiente de tus avances!"

    return render_template('dashboard/index.html', 
                           total_pacientes=total_pacientes,
                           crecimiento_pacientes=crecimiento_pacientes,
                           valoraciones_mes=valoraciones_mes,
                           promedio_diario=promedio_diario,
                           pacientes_seguimiento=pacientes_seguimiento,
                           pacientes_sin_valoracion=pacientes_sin_valoracion,
                           citas_del_dia=citas_del_dia,
                           pendientes_por_agendar=pendientes_por_agendar,
                           seguimiento_14_15=seguimiento_14_15,
                           actividad_reciente=actividad_reciente,
                           contenido_plantilla=contenido_plantilla,
                           datetime=datetime)

@main.route('/dashboard/marcar-seguimiento/<int:valoracion_id>', methods=['POST'])
@login_required
def marcar_seguimiento(valoracion_id):
    try:
        val = ValoracionAntropometrica.query.get(valoracion_id)
        if not val:
            return jsonify({'success': False, 'message': 'Valoración no encontrada'}), 404
        
        val.seguimiento_15d_enviado = True
        val.fecha_seguimiento_15d = datetime.now()

        # Registrar en la bitácora de acompañamiento WhatsApp del paciente
        mensaje_enviado = request.json.get('mensaje', 'Hola, te escribo para dar seguimiento a tu plan nutricional a los 14-15 días.') if request.is_json else 'Seguimiento de 14-15 días enviado.'
        BitacoraContacto.registrar(
            paciente_id=val.paciente_id,
            usuario_id=current_user.id if hasattr(current_user, 'id') else None,
            mensaje=mensaje_enviado
        )

        db.session.commit()
        return jsonify({'success': True, 'message': 'Seguimiento marcado como enviado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/dashboard/omitir-seguimiento/<int:valoracion_id>', methods=['POST'])
@login_required
def omitir_seguimiento(valoracion_id):
    try:
        val = ValoracionAntropometrica.query.get(valoracion_id)
        if not val:
            return jsonify({'success': False, 'message': 'Valoración no encontrada'}), 404
        
        val.seguimiento_15d_enviado = True
        val.fecha_seguimiento_15d = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Seguimiento omitido correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


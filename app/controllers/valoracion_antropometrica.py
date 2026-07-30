from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.valoracion_antropometrica import ValoracionAntropometrica
from app.models.paciente import Paciente
from app.models.cita import Cita
from app.utils.helpers import safe_float, safe_int, validar_campos
from datetime import datetime, date
from app import db_orm as db

valoracion = Blueprint('valoracion', __name__, url_prefix='/valoraciones')

@valoracion.route('/paciente/<int:paciente_id>/nueva', methods=['GET', 'POST'])
def nueva_valoracion(paciente_id):
    paciente = Paciente.obtener_por_id(paciente_id)
    if not paciente:
        flash('Paciente no encontrado', 'error')
        return redirect(url_for('pacientes.lista_pacientes'))

    if request.method == 'POST':
        # 1. Validar presencia de campos obligatorios en el Backend
        campos_requeridos = [
            'numero_cita', 'fecha', 'estatura', 'peso', 'cintura', 'torax', 
            'brazo', 'cadera', 'pierna', 'pantorrilla', 'tension_arterial', 
            'frecuencia_cardiaca', 'bicep', 'tricep', 'suprailiaco', 
            'subescapular', 'grasa', 'imc', 'porcentaje_grasa'
        ]
        
        errores = validar_campos(request.form, campos_requeridos)
        
        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('valoraciones/nueva_valoracion.html', paciente=paciente, form_data=request.form)

        # 2. Casteo seguro de tipos con manejo de excepciones detallado
        try:
            datos = {
                'numero_cita': safe_int(request.form['numero_cita']),
                'fecha': request.form['fecha'].strip(),
                'estatura': safe_float(request.form['estatura']),
                'peso': safe_float(request.form['peso']),
                'imc': safe_float(request.form['imc']),
                'grasa': safe_float(request.form['grasa']),
                'cintura': safe_float(request.form['cintura']),
                'torax': safe_float(request.form['torax']),
                'brazo': safe_float(request.form['brazo']),
                'cadera': safe_float(request.form['cadera']),
                'pierna': safe_float(request.form['pierna']),
                'pantorrilla': safe_float(request.form['pantorrilla']),
                'tension_arterial': request.form['tension_arterial'].strip(),
                'frecuencia_cardiaca': safe_int(request.form['frecuencia_cardiaca']),
                'bicep': safe_float(request.form['bicep']),
                'tricep': safe_float(request.form['tricep']),
                'suprailiaco': safe_float(request.form['suprailiaco']),
                'subescapular': safe_float(request.form['subescapular']),
                'femoral': safe_float(request.form.get('femoral'), None) if request.form.get('femoral') else None,
                'porcentaje_grasa': safe_float(request.form['porcentaje_grasa'])
            }
        except ValueError as e:
            flash(f"Error de formato: Algunos campos numéricos contienen valores inválidos.", 'error')
            return render_template('valoraciones/nueva_valoracion.html', paciente=paciente, form_data=request.form)
        except Exception as e:
            flash(f"Ocurrió un error inesperado al procesar los datos: {str(e)}", 'error')
            return render_template('valoraciones/nueva_valoracion.html', paciente=paciente, form_data=request.form)

        exito, mensaje = ValoracionAntropometrica.crear(paciente_id, datos)
        if exito:
            # Buscar cita pendiente para el paciente en la fecha actual o en la fecha de la consulta
            try:
                fecha_consulta = datetime.strptime(datos['fecha'], '%Y-%m-%d').date() if isinstance(datos['fecha'], str) else datos['fecha']
            except ValueError:
                fecha_consulta = date.today()

            cita_hoy = Cita.query.filter_by(
                paciente_id=paciente_id,
                fecha=fecha_consulta
            ).filter(
                (Cita.estado == 'pendiente') | (Cita.estatus == 'Programada') | (Cita.estatus.is_(None))
            ).first()

            if cita_hoy:
                cita_hoy.estado = 'completada'
                cita_hoy.estatus = 'Atendida'
                db.session.commit()

            flash(mensaje, 'success')
            return redirect(url_for('valoracion.lista_valoraciones', paciente_id=paciente_id))
        else:
            flash(mensaje, 'error')

    return render_template('valoraciones/nueva_valoracion.html', paciente=paciente)

@valoracion.route('/paciente/<int:paciente_id>/lista')
def lista_valoraciones(paciente_id):
    if paciente_id == 0:
        return redirect(url_for('valoracion.todas_valoraciones'))
    
    paciente = Paciente.obtener_por_id(paciente_id)
    if not paciente:
        flash('Paciente no encontrado', 'error')
        return redirect(url_for('pacientes.lista_pacientes'))

    valoraciones = ValoracionAntropometrica.obtener_por_paciente(paciente_id)
    return render_template('valoraciones/lista_valoraciones.html', paciente=paciente, valoraciones=valoraciones)

@valoracion.route('/')
def todas_valoraciones():
    valoraciones = ValoracionAntropometrica.obtener_todas()
    return render_template('valoraciones/todas_valoraciones.html', valoraciones=valoraciones)

@valoracion.route('/valoraciones/<int:valoracion_id>')
def detalle_valoracion(valoracion_id):
    valoracion = ValoracionAntropometrica.obtener_por_id(valoracion_id)
    if not valoracion:
        flash('Valoración no encontrada', 'error')
        return redirect(url_for('valoracion.todas_valoraciones'))
    
    paciente = Paciente.obtener_por_id(valoracion.paciente_id)
    historial_valoraciones = ValoracionAntropometrica.obtener_por_paciente(valoracion.paciente_id)
    
    # Encontrar la valoración anterior
    valoracion_anterior = None
    for i, v in enumerate(historial_valoraciones):
        if v.id == valoracion_id and i + 1 < len(historial_valoraciones):
            valoracion_anterior = historial_valoraciones[i + 1]
            break
    
    return render_template('valoraciones/detalle_valoracion.html', 
                            valoracion=valoracion, 
                            valoracion_anterior=valoracion_anterior,
                            paciente=paciente,
                            historial_valoraciones=historial_valoraciones)

@valoracion.route('/valoraciones/<int:valoracion_id>/editar', methods=['GET', 'POST'])
def editar_valoracion(valoracion_id):
    valoracion = ValoracionAntropometrica.obtener_por_id(valoracion_id)
    if not valoracion:
        flash('Valoración no encontrada', 'error')
        return redirect(url_for('valoracion.todas_valoraciones'))

    paciente = Paciente.obtener_por_id(valoracion['paciente_id'])

    if request.method == 'POST':
        datos = {
            'fecha': request.form['fecha'],
            'estatura': request.form['estatura'],
            'peso': request.form['peso'],
            'imc': request.form['imc'],
            'grasa': request.form['grasa'],
            'cintura': request.form['cintura'],
            'torax': request.form['torax'],
            'brazo': request.form['brazo'],
            'cadera': request.form['cadera'],
            'pierna': request.form['pierna'],
            'pantorrilla': request.form['pantorrilla'],
            'tension_arterial': request.form['tension_arterial'],
            'frecuencia_cardiaca': request.form['frecuencia_cardiaca'],
            'bicep': request.form['bicep'],
            'tricep': request.form['tricep'],
            'suprailiaco': request.form['suprailiaco'],
            'subescapular': request.form['subescapular'],
            'femoral': request.form.get('femoral', ''),  # Opcional para hombres
            'porcentaje_grasa': request.form['porcentaje_grasa']
        }

        exito, mensaje = ValoracionAntropometrica.actualizar(valoracion_id, datos)
        if exito:
            flash(mensaje, 'success')
            return redirect(url_for('valoracion.detalle_valoracion', valoracion_id=valoracion_id))
        else:
            flash(mensaje, 'error')

    return render_template('valoraciones/editar_valoracion.html', valoracion=valoracion, paciente=paciente)

@valoracion.route('/valoraciones/<int:valoracion_id>/eliminar', methods=['POST'])
def eliminar_valoracion(valoracion_id):
    valoracion = ValoracionAntropometrica.obtener_por_id(valoracion_id)
    if not valoracion:
        flash('Valoración no encontrada', 'error')
        return redirect(url_for('valoracion.todas_valoraciones'))

    exito, mensaje = ValoracionAntropometrica.eliminar(valoracion_id)
    if exito:
        flash(mensaje, 'success')
        return redirect(url_for('valoracion.lista_valoraciones', paciente_id=valoracion['paciente_id']))
    else:
        flash(mensaje, 'error')
        return redirect(url_for('valoracion.detalle_valoracion', valoracion_id=valoracion_id))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models.plantilla import PlantillaMensaje
from app import db_orm as db

plantillas_bp = Blueprint('plantillas', __name__, url_prefix='/plantillas-mensajes')

@plantillas_bp.route('/')
@login_required
def index():
    plantillas = PlantillaMensaje.query.all()
    return render_template('plantillas/index.html', plantillas=plantillas)

@plantillas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        contenido = request.form.get('contenido')
        esta_activa = True if request.form.get('esta_activa') else False

        if not titulo or not contenido:
            flash('El título y el contenido son obligatorios.', 'error')
            return redirect(url_for('plantillas.nueva'))

        if esta_activa:
            # Desactivar las demás
            PlantillaMensaje.query.update({PlantillaMensaje.esta_activa: False})

        nueva_p = PlantillaMensaje(titulo=titulo, contenido=contenido, esta_activa=esta_activa)
        db.session.add(nueva_p)
        db.session.commit()
        flash('Plantilla creada correctamente.', 'success')
        return redirect(url_for('plantillas.index'))

    return render_template('plantillas/form.html', plantilla=None)

@plantillas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    plantilla = PlantillaMensaje.query.get_or_404(id)
    if request.method == 'POST':
        plantilla.titulo = request.form.get('titulo')
        plantilla.contenido = request.form.get('contenido')
        esta_activa = True if request.form.get('esta_activa') else False

        if esta_activa and not plantilla.esta_activa:
            PlantillaMensaje.query.update({PlantillaMensaje.esta_activa: False})

        plantilla.esta_activa = esta_activa
        db.session.commit()
        flash('Plantilla actualizada correctamente.', 'success')
        return redirect(url_for('plantillas.index'))

    return render_template('plantillas/form.html', plantilla=plantilla)

@plantillas_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    try:
        plantilla = PlantillaMensaje.query.get_or_404(id)
        db.session.delete(plantilla)
        db.session.commit()
        flash('Plantilla eliminada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la plantilla: {str(e)}', 'error')
    return redirect(url_for('plantillas.index'))

@plantillas_bp.route('/activar/<int:id>', methods=['POST'])
@login_required
def activar(id):
    try:
        PlantillaMensaje.query.update({PlantillaMensaje.esta_activa: False})
        plantilla = PlantillaMensaje.query.get_or_404(id)
        plantilla.esta_activa = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Plantilla activada para envíos'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

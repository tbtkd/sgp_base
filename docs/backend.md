# Documentación del Backend - Sistema de Gestión de Pacientes y Nutrición (SGPN)

## 1. Arquitectura y Estructura
El backend está desarrollado en **Python (Flask)** utilizando el patrón modular de **Blueprints**. Los controladores gestionan la lógica de negocio, validación defensiva e interacción con la base de datos mediante **Flask-SQLAlchemy**.

### Blueprints Principales:
- `auth`: Gestión de autenticación de usuarios (`/login`, `/logout`, registro y control de estatus).
- `dashboard`: Indicadores, pacientes del día y métricas generales.
- `pacientes`: CRUD de pacientes, historial clínico, agendamiento de citas, pagos y bitácora de WhatsApp.
- `valoraciones`: Módulo de valoraciones antropométricas por pestañas con validación defensiva.
- `plantillas`: Gestión y catálogo de plantillas predeterminadas de WhatsApp.

## 2. Mecanismo de Auto-Migración en Caliente y Resiliencia
Para garantizar la operación sin fallas en entornos empaquetados (`.exe` con PyInstaller), el sistema incluye una rutina de auto-migración en `app/__init__.py`:
- **Inspección de Esquema**: Utiliza `sqlalchemy.inspect(db.engine)` para verificar tablas y columnas en la base de datos SQLite.
- **Inyección Dinámica**: Si detecta campos faltantes (ej. estatus, motivos de cancelación), ejecuta sentencias `ALTER TABLE` seguras sin pérdida de datos.
- **Respaldo Preventivo**: Genera copias de respaldo del archivo `.db` antes de realizar alteraciones estructurales.

## 3. Política de Instancia Única y Prevención de Bloqueos (`database is locked`)
- **Validación en `run.py`**: Comprueba mediante sockets si el puerto de ejecución está ocupado.
- **Ventana de Advertencia**: Muestra una interfaz HTML estilizada (`error_inicio.html`) cuando la aplicación ya se encuentra abierta.

## 4. Endpoints Clave y Gestión de Estados
- `POST /citas/<id>/cambiar-estatus`: Actualiza el estatus de las citas (`Programada`, `Asistido`, `No Asistió`, `Cancelada`).
- Sincronización automática de citas a `'Asistido'` al registrar valoraciones antropométricas o historiales clínicos.
- `respaldar_codigo.py`: Script automatizado para empaquetar todo el código fuente en archivos ZIP con marca temporal.

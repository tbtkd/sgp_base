# Arquitectura técnica — versión 1.6.3

## Componentes

- `app/__init__.py`: fábrica Flask, extensiones, blueprints, errores, cabeceras y ciclo de arranque.
- `app/db.py`: ruta persistente, respaldo nativo y migración aditiva de columnas.
- `app/config.py`: secreto, cookies, límites y configuraciones de ambiente.
- `app/core/validators.py`: normalización y validación autoritativa del servidor.
- `app/core/auth.py`, `app/core/security.py` y `app/core/password_recovery.py`: sesión, RBAC, limitación de intentos y recuperación local.
- `app/models/`: esquema SQLAlchemy.
- `app/controllers/`: transacciones y casos de uso.
- `app/templates/` y `app/static/`: interfaz actual preservada y adaptada al dominio clínico general.

El dashboard agrega consultas de lectura acotadas para altas de seis meses, pacientes recientes y expedientes pendientes. La gráfica se genera como SVG local a partir de una serie construida en servidor; no incorpora bibliotecas de visualización ni servicios externos.

La cabecera usa HTML nativo (`hidden`) como estado seguro del menú de cuenta y JavaScript local para su interacción. Alpine sigue presente en componentes legados, pero ya no determina si el detalle de identidad aparece durante la carga.

## Persistencia portable

```mermaid
flowchart TD
    A["Inicio"] --> B{"¿PyInstaller?"}
    B -- No --> C["proyecto/instance/pacientes.db"]
    B -- Sí --> D["directorio del EXE/instance/pacientes.db"]
    C --> E["Respaldo SQLite"]
    D --> E
    E --> F["backups/ últimos 10"]
```

`_MEIPASS` se utiliza solamente para plantillas y recursos incluidos en el ejecutable. Nunca recibe la base de datos o el secreto.

## Esquema clínico

- `Paciente` 1:1 `HistorialClinico`.
- `Paciente` 1:N `ValoracionAntropometrica` (consulta clínica general conservando la tabla histórica).
- `Paciente` 1:N `Cita`, `Pago` y `BitacoraContacto`.
- `ValoracionAntropometrica` 1:N `Receta`; `Receta` 1:N `RecetaMedicamento`.
- `Receta` 0..1:0..1 `Receta` como documento sustituido/reemplazo.
- `Usuario` 1:N `Receta` como emisor, conservando además una instantánea profesional.
- `Usuario` 1:N `AuditLog`.

La denominación interna `valoracion_antropometrica` se conserva para compatibilidad; en la interfaz representa una consulta clínica y sus campos antropométricos son opcionales.

Cada receta ordinaria emitida es un documento independiente e inmutable. La consulta admite un original, recetas adicionales y sustituciones versionadas. Una sustitución marca el folio anterior como no vigente sin reescribirlo y enlaza ambos documentos. Los snapshots almacenan nombre, nacimiento y alergias del paciente, además de nombre, cédula, perfil, establecimiento y domicilio del profesional. La bitácora sólo conserva identificadores, tipo, versión y conteos, nunca el contenido farmacológico.

## Migraciones compatibles

`init_db()` crea tablas faltantes y compara cada tabla conocida mediante `PRAGMA table_info`. Solo ejecuta `ALTER TABLE ... ADD COLUMN` cuando la columna nueva es nullable o posee un valor predeterminado. Si falta una llave primaria o una columna nueva no puede añadirse sin inventar datos, el arranque se detiene.

Este mecanismo no elimina ni renombra columnas. La versión 1.6.0 incorpora una excepción controlada y versionada para retirar la restricción única legada `recetas.valoracion_id`: reconstruye sólo esa tabla dentro de una transacción, conserva todas sus filas, recrea llaves/índices y ejecuta `foreign_key_check` e `integrity_check`. El respaldo de arranque ocurre antes de la migración. Cualquier cambio estructural futuro requiere el mismo nivel de copia, prueba y verificación.

Las bases legadas con roles `Admin/Nutricionista/Asistente` se interpretan como `admin/medico/recepcion` sin modificar su restricción histórica; las instalaciones nuevas almacenan exclusivamente el catálogo actual.

Si existe `instance/sgpn.db` y aún no existe `pacientes.db`, la API nativa de SQLite crea una copia íntegra en el nombre nuevo y conserva el archivo legado como recuperación adicional. La clave histórica `.session_secret` se migra de igual forma a `.secret_key`.

## Seguridad

- Todas las rutas funcionales requieren autenticación.
- RBAC en backend: `admin`, `medico`, `recepcion`.
- CSRF para operaciones mutables.
- Scrypt para contraseñas.
- `auth_version` invalida sesiones después de un cambio/restablecimiento.
- Credenciales temporales obligan a elegir una definitiva; la recuperación local sólo opera sobre administradores con acceso al equipo.
- Bloqueo de cuenta y de IP después de cinco fallos.
- Cabeceras CSP, anti-frame, `nosniff`, políticas de origen y no-cache.
- Errores genéricos con `X-Request-ID`.
- Auditoría con usuario, módulo, acción, entidad, IP y resultado.
- Transacciones completas en controladores; los modelos no hacen `commit`.

## Dependencias

El archivo de ejecución conserva solo paquetes utilizados directamente: Flask, Flask-Login, Flask-SQLAlchemy, Flask-WTF, `defusedxml`, `openpyxl` y Waitress. Reducirlo a Flask/OpenPyXL/PyInstaller rompería autenticación, ORM, CSRF y el servidor local; PyInstaller permanece correctamente separado en `requirements-build.txt`.

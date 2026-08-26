# Sistema de Expediente Clínico y Gestión de Pacientes

Versión **1.10.1**. Aplicación local para consultorios médicos, dentales, nutricionales y otros servicios de salud. Generaliza el expediente, las consultas, los signos vitales, las citas, los pagos operativos, la receta ordinaria y el seguimiento por WhatsApp.

## Funcionalidad

- Expediente con datos personales, ocupación, dirección y contacto de emergencia.
- Antecedentes patológicos, heredofamiliares, alergias, medicación, hábitos y notas.
- Consultas con síntomas, signos vitales, diagnóstico, plan e indicaciones clínicas.
- Índice de Consultas con una sola fila por paciente, última nota determinista, búsqueda parcial sin distinguir mayúsculas ni acentos, orden por fecha y paginación de servidor.
- Turno diario global de consultas, asignado por el servidor en secuencia `1..n` y reiniciado para cada fecha.
- Receta médica ordinaria independiente para Medicina/Odontología, con folios originales, adicionales y sustituciones trazables.
- Captura de medicamentos con altas nuevas en la parte superior y orden clínico final estable `1, 2, 3…`.
- Receta A4 compacta, sin tarjetas repetidas, con densidad automática para tratamientos extensos y saltos de página por medicamento.
- Firma autógrafa única y centrada; identificación profesional completa exclusivamente en el encabezado.
- Impresión de receta con márgenes clínicos propios y sin fecha, título, URL o paginación agregados por navegadores Chromium modernos.
- Antropometría y pliegues opcionales, habilitados exclusivamente para perfiles de Nutrición.
- Pagos monetarios exactos en centavos, moneda MXN, folio único, responsable, relación explícita y opcional con cita y prevención de doble envío.
- Historial inmutable de pagos por paciente, último pago vigente, cancelación administrativa trazable y conservación del movimiento original.
- Módulo global de Pagos para Administración y Recepción, con total vigente, desglose por método, búsqueda por nombre completo o términos parciales sin distinguir mayúsculas ni acentos, filtros y paginación.
- Reporte administrativo diario o mensual y exportación CSV segura del filtro o del historial individual, con límite de 10,000 filas y neutralización de fórmulas.
- Usuarios con roles `admin`, `medico` y `recepcion`, separados de su perfil profesional.
- Perfiles clínicos: Medicina general, Odontología/Dentista y Nutrición.
- Nombre, perfil y cédula del autor conservados dentro de cada consulta nueva.
- Auditoría administrativa de accesos y operaciones críticas.
- Recursos visuales y diálogos completamente locales, sin CDN ni conexión a Internet.
- CSP estricta con nonce por respuesta, sin `unsafe-inline`, scripts remotos o atributos ejecutables.
- Respaldo verificado después de operaciones críticas y panel administrativo para crear, verificar, descargar y restaurar copias internas.
- Enlaces directos a WhatsApp e impresión limpia de notas y recetas como PDF.
- Shell clínico responsive con búsqueda global, sede local, notificaciones vacías explícitas, breadcrumb y tema claro/oscuro persistente.
- Identidad y menú de cuenta concentrados al pie del sidebar; el botón `...` despliega datos profesionales, cambio de contraseña y cierre de sesión.
- Menú de cuenta cerrado de forma nativa al cargar, con apertura explícita y cierre por Escape o clic exterior.
- Un solo icono institucional para navegador, interfaz y ejecutable Windows.
- Cambio propio de contraseña, restablecimiento administrativo, protección contra perder accidentalmente Administración y recuperación local para el responsable del equipo.
- Pestañas clínicas locales, estados vacíos accionables y KPIs coherentes.
- Dashboard operativo con agenda, gráfica local, pacientes recientes, pendientes y actividad basada exclusivamente en datos persistidos; Próximas citas y Acompañamiento Intermedio comparten una fila adaptable, sin duplicar alertas ni mostrar ingresos.
- KPI accionables: cada tarjeta conserva su resumen, enlaza al módulo relacionado y permite Nuevo paciente, Agendar cita o Nueva consulta sin una fila duplicada.
- Agenda rápida desde el KPI o el módulo operativo: búsqueda bajo demanda de paciente activo —sin precargar el padrón—, ficha única, calendario de 21 días, consulta de fechas posteriores y selección visual de horarios disponibles.
- Módulo **Agenda y citas** con vistas Día/Semana, navegación por periodo, resumen de estados, reagenda sobre el mismo registro, cancelación, inasistencia, cierre como atendida e inicio de consulta según rol.
- Estados de cita validados en servidor: una cita futura no puede cerrarse como atendida/inasistente y una cita cerrada no puede reabrirse.
- Recepción administra la agenda sin recibir motivos clínicos ni accesos a notas; los perfiles clínicos conservan el inicio de consulta.
- Topbar compacto que permanece visible mientras el área principal se desplaza, sin alterar el sidebar ni las vistas de impresión.
- Formulario clínico con pestañas, campos y superficies suaves adaptados a la paleta oscura, sin contornos agresivos ni controles claros de bajo contraste.
- Sidebar con tipografía e iconografía legibles, módulos planificados discretos y estados interactivos de tablas, tarjetas y botones coherentes en tema oscuro.
- Resumen del historial ordenado por relevancia clínica: Historial médico, Alimentación y Actividad física.
- El pendiente **Sin consulta reciente** se calcula y muestra sólo para perfiles de Nutrición.
- Navegación que diferencia enlaces operativos, acceso contextual funcional a recetas, grupo desplegable de Administración y módulos planificados sin crear rutas ficticias.
- Importación XLSX defensiva para expedientes antropométricos históricos, visible y autorizada exclusivamente para perfiles de Nutrición.
- Detalle progresivo del paciente: datos principales y seguimiento siempre visibles; campos complementarios sólo cuando fueron capturados y un único aviso accionable cuando faltan.
- Pendientes desplegables con contraste AA explícito en tema oscuro, incluidos texto secundario, hover y foco de teclado.

## Instalación

Requiere Python 3.10 o posterior.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

En Linux/macOS, la activación es `source .venv/bin/activate`.

### Actualización de una instalación existente

La opción más segura es descomprimir cada versión en una carpeta nueva y copiar únicamente `instance/` y `backups/` después de conservar un respaldo. Al extraer un ZIP sobre una carpeta anterior, Windows reemplaza archivos incluidos pero no elimina archivos que dejaron de formar parte del proyecto.

No copies las pruebas nuevas sobre una carpeta de código anterior. Si la prueba de seguridad menciona `style=`, `onclick=` u otro atributo no permitido, la salida indicará el archivo y la línea exactos. En la entrega 1.10.1 limpia no existen esos atributos; el caso normalmente indica que quedaron plantillas de una versión anterior. Descomprime el ZIP completo en una carpeta nueva y vacía, crea un entorno virtual nuevo y vuelve a ejecutar las pruebas.

Si actualizas sobre la misma carpeta, ejecuta después:

```powershell
python scripts\cleanup_project.py
```

La utilidad elimina únicamente `app/static/img/logo.svg`, la hoja legada no referenciada `app/static/css/components/_sidebar.css`, cachés de Python y cachés de herramientas conocidas. No recorre ni modifica `.venv`, `instance`, `backups`, bases de datos, secretos o registros. También se ejecuta automáticamente antes de construir el ejecutable.

## Inicialización y ejecución

Crear el primer administrador:

```bash
python seed_admin.py
```

Después, iniciar el servidor local:

```bash
python run.py
```

La aplicación escucha exclusivamente en `http://127.0.0.1:5000/`. También se conserva el alta inicial de un solo uso desde `/setup` cuando no existe ningún usuario.

Si se olvida la contraseña, otro administrador puede generar una credencial temporal desde **Gestión de usuarios**. Cuando ningún administrador puede ingresar, en el mismo equipo se utiliza:

```bash
python run.py --reset-password NOMBRE_USUARIO
```

El ejecutable admite `SistemaPacientes.exe --reset-password NOMBRE_USUARIO`. La recuperación local sólo permite cuentas administradoras, invalida sesiones anteriores y obliga a cambiar nuevamente la contraseña después del login.

Una cuenta administradora conserva ese tipo de acceso aunque también atienda pacientes: basta elegir su **Perfil clínico**. El sistema impide que cambie su propio rol o se desactive por accidente. Si una instalación anterior quedó sin ninguna cuenta de Administración activa, se recupera una cuenta existente con:

```bash
python run.py --recover-admin NOMBRE_USUARIO
```

El ejecutable admite también `SistemaPacientes.exe --recover-admin NOMBRE_USUARIO`. Este segundo comando se rechaza mientras todavía exista otra cuenta de Administración activa.

Consulta el procedimiento y su modelo de seguridad en [docs/RECUPERACION_ACCESO.md](docs/RECUPERACION_ACCESO.md).

Si el arranque falla, la consola muestra la causa concreta y la ruta de `instance/logs/startup.log`. En PowerShell también puede consultarse el registro de Flask con:

```powershell
Get-Content .\instance\logs\app.log -Tail 80
Get-Content .\instance\logs\startup.log -Tail 80
```

Para una inicialización automatizada se admiten `SGPN_ADMIN_USERNAME`, `SGPN_ADMIN_PASSWORD`, `SGPN_ADMIN_NAME`, `SGPN_ADMIN_LASTNAME`, `SGPN_ADMIN_MATERNAL` y `SGPN_ADMIN_EMAIL`.

### Datos de demostración opcionales

Para validar pantallas sin capturar todo manualmente, trabaja sobre una copia o base de pruebas y ejecuta:

```powershell
python seed_demo.py --confirm
```

El comando agrega cuentas ficticias para Administración, Medicina, Odontología, Nutrición y Recepción, además de seis pacientes, historiales, nueve consultas, siete citas, dieciocho pagos operativos y una receta de tres medicamentos. También genera `demo_data/expediente_antropometrico_demo.xlsx`. La contraseña aleatoria de las cuentas nuevas se muestra una sola vez. Nada se carga automáticamente y una segunda ejecución no duplica el conjunto. Consulta [demo_data/README.md](demo_data/README.md) y la [matriz de escenarios de Pagos](demo_data/ESCENARIOS_PAGOS_1_10.md); elimina o desactiva estas cuentas antes de utilizar información real.

## Persistencia y respaldos

- Ejecución normal: `instance/pacientes.db` dentro del proyecto.
- PyInstaller: `instance/pacientes.db` junto al ejecutable, nunca dentro de `_MEIPASS`.
- Ruta personalizada: variable `SGPN_DATA_DIR`.
- Secreto de sesión: `instance/.secret_key`, generado con 32 bytes criptográficos.
- Respaldos: `backups/pacientes_backup_YYYYMMDD_HHMMSS_microsegundos.db`.
- Retención: últimas 10 copias verificadas mediante `PRAGMA integrity_check`.
- Frecuencia: al iniciar y después de una mutación crítica confirmada; una solicitud rechazada no genera copia.

Administración dispone de **Administración → Respaldos**. Restaurar exige la contraseña actual y la frase `RESTAURAR`; antes de reemplazar la base se crea otra copia, se valida el esquema y al finalizar se cierra la sesión. Una descarga contiene datos personales y clínicos: debe tratarse como la base activa. Consulta [docs/ENDURECIMIENTO_LOCAL_1_10_1.md](docs/ENDURECIMIENTO_LOCAL_1_10_1.md).

Si una base muy antigua no contiene el correo de sus usuarios, la migración conserva las cuentas y asigna valores únicos `usuario-migrado-<id>@local.invalid`. Son marcadores locales que no reciben mensajes y deben reemplazarse desde el panel **Usuarios**.

Al actualizar a 1.7.2, las consultas existentes se numeran de forma determinista por fecha, momento de creación e identificador. Se crea una restricción única sobre `(fecha, numero_cita)` sin borrar consultas. El turno es una referencia histórica: si una nota se elimina o cambia de fecha puede quedar un hueco, por lo que los reportes deben contar registros y no usar el turno máximo como total definitivo.

Al actualizar a 1.10.0, la tabla `pagos` se reconstruye dentro de una migración transaccional verificada. Los importes válidos se convierten a `monto_centavos`, reciben folio y clave de operación, y dejan de eliminarse en cascada con el paciente. Los pagos anteriores sin importe, concepto, método o moneda confiable se conservan como **Requiere revisión**, permanecen visibles y no se suman en los totales. Un pago nuevo nunca entra en ese estado: los datos incompletos se rechazan antes de guardar. Administración revisa esos casos contra comprobantes; cancela el registro incompleto y, si el cobro se confirma, registra uno nuevo con los datos comprobados. El campo `monto` se mantiene temporalmente como espejo de compatibilidad, pero ningún cálculo nuevo depende de `Float`.

El directorio que contiene el ejecutable debe ser escribible. Los datos, respaldos y secretos están excluidos del paquete y del control de versiones.

## Impresión de notas clínicas y recetas

Desde el detalle de una consulta selecciona **Imprimir nota / PDF**. La aplicación abre una hoja A4 independiente; después pulsa **Imprimir / guardar PDF** y elige **Guardar como PDF**. La nota imprimible no depende de Tailwind, Alpine ni recursos CDN.

La nota clínica y la receta son documentos distintos. Cuando el usuario tiene perfil de Medicina general u Odontología, cédula y domicilio profesional, el detalle ofrece **Generar receta**. El formulario exige por medicamento denominación genérica, presentación, dosis, vía, frecuencia y duración. **Agregar** inserta la nueva tarjeta arriba para no obligar a regresar al inicio; un orden de captura oculto, validado por el servidor, hace que la receta emitida siempre se muestre en secuencia `1, 2, 3…`. La salida conserva una instantánea del paciente y del profesional.

La receta impresa agrupa cada medicamento en un bloque tipográfico breve: nombre y presentación; vía y cantidad cuando exista; dosis, frecuencia y duración; e indicaciones sólo cuando fueron capturadas. No usa cajas entre medicamentos, activa una densidad mayor desde seis elementos y evita dividir un medicamento entre páginas. El nombre, perfil, cédula y domicilio del profesional aparecen una sola vez en el encabezado; el rótulo visible se simplifica a **Domicilio**. Al final queda únicamente una línea centrada para la firma autógrafa, separada suficientemente del tratamiento. En Opera, Chrome y Edge modernos, la receta sustituye las cajas de margen del navegador para evitar fecha, título, URL y paginación automáticos, conservando 14 mm arriba y 12 mm en los demás lados. En navegadores sin soporte de cajas de margen todavía debe desactivarse manualmente **Encabezados y pies de página**. La receta implementada es únicamente **ordinaria**: debe revisarse, imprimirse y llevar firma autógrafa. Una receta emitida no se edita; una corrección utiliza la acción ámbar **Sustituir**, crea un folio nuevo y marca el anterior como no vigente. Desde una misma consulta pueden emitirse recetas adicionales con folio independiente. No admite estupefacientes, psicotrópicos ni otros flujos sujetos a receta especial. Consulta [docs/RECETA_COMPACTA_1_7_3.md](docs/RECETA_COMPACTA_1_7_3.md), [docs/FIRMA_FAVICON_RECETA_1_7_4.md](docs/FIRMA_FAVICON_RECETA_1_7_4.md), [docs/IMPRESION_RECETA_LIMPIA_1_7_5.md](docs/IMPRESION_RECETA_LIMPIA_1_7_5.md) y [docs/RECETA_MEDICA_MEXICO.md](docs/RECETA_MEDICA_MEXICO.md) antes de usarla con datos reales.

## Roles

| Función | admin | medico | recepcion |
| --- | --- | --- | --- |
| Pacientes, citas y pagos | Sí | Sí | Sí |
| Módulo global de Pagos | Sí | No | Sí |
| Reporte y exportación de Pagos | Sí | No | No |
| Cancelar un pago | Sí | No | No |
| Expediente clínico | Sí | Sí | No |
| Consultas, diagnóstico e indicaciones | Sí | Sí | No |
| Emitir receta ordinaria | Sólo con perfil Medicina/Odontología y datos completos | Sólo con perfil Medicina/Odontología y datos completos | No |
| Antropometría e importación | Sólo con perfil Nutrición | Sólo con perfil Nutrición | No |
| Usuarios y auditoría | Sí | No | No |
| Crear, verificar, descargar o restaurar respaldos | Sí | No | No |

## Pruebas y calidad

`pytest` es el único comando oficial y también descubre los casos heredados escritos con `unittest`, evitando ejecutar dos veces la misma cobertura:

```bash
python -m pytest -q
ruff check app tests run.py seed_admin.py seed_demo.py
bandit -q -r app run.py seed_admin.py seed_demo.py -x app/static,app/templates
pip-audit -r requirements.txt
```

La aceptación principal incluye **122 casos** (15 heredados de `unittest`). Existe un caso E2E adicional que eleva el total a 123 cuando Playwright y Chromium están instalados; de lo contrario se omite de forma explícita. El detalle se encuentra en [docs/TEST_MATRIX.md](docs/TEST_MATRIX.md). Las instrucciones para PowerShell están en [docs/EJECUCION_PRUEBAS.md](docs/EJECUCION_PRUEBAS.md).

## Compilación para Windows

```bat
pip install -r requirements-build.txt
build_exe.bat
```

El ejecutable se genera sin base de datos, secretos, registros ni respaldos. `PyInstaller` se mantiene como dependencia de compilación, no de ejecución.

## Seguridad y límites

Consulta [SECURITY_REVIEW.md](SECURITY_REVIEW.md) antes de utilizar datos reales. La 1.10.1 alcanza el mínimo técnico de aplicación definido para un piloto local controlado: autenticación/roles, CSRF, validación, auditoría, CSP local y restauración verificada. No equivale a una autorización para exponerla en red; siguen pendientes cifrado en reposo, HTTPS, gobernanza de privacidad y evaluación legal/operativa.

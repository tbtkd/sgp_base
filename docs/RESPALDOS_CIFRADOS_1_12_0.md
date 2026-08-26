# Copias protegidas y llave de recuperación — versión 1.12.0

## Qué cambia

Todas las copias nuevas se guardan con extensión `.sgpnbak` y cifrado autenticado AES-256-GCM. El contenido no puede leerse como una base SQLite y cualquier alteración, truncamiento o llave incorrecta hace que la comprobación y la recuperación se rechacen sin sustituir la información actual.

La aplicación crea una llave independiente en `instance/.backup_key`. La llave no se incluye en el ZIP, el ejecutable, la base, las copias ni los registros. El panel muestra solamente su identificador, que permite confirmar que una llave corresponde a una instalación sin revelar el secreto.

## Acción indispensable de Administración

1. Abre **Administración → Copias de seguridad**.
2. En **Llave de recuperación**, selecciona **Descargar llave**.
3. Confirma tu contraseña y escribe `DESCARGAR` exactamente.
4. Guarda el archivo en un medio privado distinto de la computadora del consultorio. Mantén al menos una copia desconectada.
5. Crea una copia protegida, descárgala y conserva juntos —pero con acceso restringido— el respaldo y la llave que comparte su identificador.

Quien posea ambos archivos puede leer toda la información respaldada. No envíes la llave por correo o mensajería ni la guardes en una carpeta pública.

## Copias de versiones anteriores

Las copias `.db` existentes siguen apareciendo como **Anterior sin cifrar** para evitar una pérdida durante la actualización. Administración puede seleccionar **Proteger copias anteriores**, confirmar su contraseña y escribir `PROTEGER`.

El sistema aplica este orden a cada archivo:

1. comprueba la copia SQLite original;
2. crea la versión cifrada;
3. descifra temporalmente y vuelve a comprobar la versión protegida;
4. elimina el original únicamente si todas las comprobaciones fueron correctas.

Una copia corrupta o que no pueda cifrarse se conserva sin cambios y se informa como pendiente.

## Recuperación en el mismo equipo

Selecciona **Recuperar**, confirma la contraseña y escribe `RESTAURAR`. Antes de sustituir la base, SGPN crea otra copia protegida del estado actual. Luego valida el cifrado, la integridad y las tablas mínimas, reemplaza la base de forma atómica y cierra la sesión.

## Recuperación en otro equipo

1. Instala la misma versión o una posterior compatible y ciérrala.
2. Copia el archivo de llave guardado como `instance/.backup_key`.
3. Copia los archivos `.sgpnbak` a `backups/`.
4. Inicia SGPN y confirma que el identificador mostrado sea el mismo del archivo de llave.
5. Usa **Comprobar** antes de **Recuperar**.

Si SGPN ya había generado una llave nueva en el equipo de destino, consérvala aparte antes de reemplazarla. Las copias creadas con llaves distintas no son intercambiables.

## Llave administrada por el entorno

Una instalación administrada puede definir `SGPN_BACKUP_KEY` con una llave Base64 URL-safe de 32 bytes. En ese caso SGPN no escribe ni permite descargar la llave desde la interfaz; su custodia y recuperación pertenecen al responsable de la instalación.

## Pérdida de la llave

No existe contraseña maestra ni puerta trasera. Si se pierden la llave local y todas sus copias externas, los archivos `.sgpnbak` asociados no pueden recuperarse. La base activa seguirá funcionando mientras permanezca intacta, por lo que debe exportarse inmediatamente una nueva copia junto con su llave vigente.

## Límite de esta fase

La versión 1.12.0 cifra los respaldos, pero `instance/pacientes.db` continúa siendo una base SQLite legible para mantener compatibilidad comprobada con Flask-SQLAlchemy, migraciones y el ejecutable Windows. Por ello la protección del archivo activo sigue dependiendo del cifrado del disco y del acceso al equipo.

No se afirma que la base activa esté cifrada. La siguiente fase de seguridad debe integrar y validar un motor SQLite con cifrado transparente —incluyendo migración, construcción Windows y recuperación— antes de permitir operación en red.

## Pruebas de seguridad

La suite valida casos correctos e incorrectos: ausencia de sesión, rol sin permiso, CSRF ausente, contraseña o frase incorrectas, nombre fuera del catálogo, copia corrupta, contenido alterado, llave equivocada, ausencia de texto clínico visible en el archivo, temporales eliminados, conversión segura de copias anteriores, descarga sensible sin caché y restauración atómica.

# Endurecimiento local y continuidad — 1.10.1

## Resultado

La versión 1.10.1 elimina las dependencias web del frontend, endurece la política de ejecución del navegador y permite administrar el ciclo completo de respaldos SQLite. El alcance es la aplicación; los requisitos físicos o del sistema operativo del equipo no forman parte de esta fase.

## Recursos locales y CSP

- `scripts/build_local_assets.py` inspecciona las clases usadas por Jinja y genera `app/static/css/utilities.css` e `icons.css`.
- `alertas.js` implementa confirmaciones accesibles mediante `<dialog>` y conserva la interfaz `Swal.fire()` usada por Agenda y Dashboard.
- El modal XLSX ya no usa Alpine. Ninguna plantilla carga Tailwind, Font Awesome, Google Fonts, Alpine o SweetAlert desde Internet.
- Cada solicitud HTML recibe un nonce aleatorio. La CSP permite sólo `script-src 'self' 'nonce-…'` y `style-src 'self' 'nonce-…'`; `script-src-attr` y `style-src-attr` son `none`.
- Los bloques internos legítimos declaran su nonce. Los eventos se registran con `addEventListener` y la presentación dinámica usa clases, atributos nativos o `<progress>`.

Para comprobar que los recursos generados corresponden a las plantillas:

```bash
python scripts/build_local_assets.py --check
```

## Respaldo posterior a operaciones críticas

`AuditLog.record()` marca las mutaciones clínicas, de usuarios, pagos, citas y recetas que terminaron con resultado `success`. Después de construir una respuesta exitosa, la aplicación crea una copia mediante `sqlite3.Connection.backup()`, ejecuta `PRAGMA integrity_check`, realiza un reemplazo temporal atómico y conserva las diez copias más recientes.

Una solicitud rechazada, duplicada o sin permiso no dispara una copia. Si el destino no está disponible, el cambio de negocio ya confirmado no se revierte: se registra la excepción y la respuesta incluye `X-SGPN-Backup: failed`. Esta decisión evita informar al usuario que su operación falló cuando los datos sí se guardaron; el administrador debe atender el registro técnico y crear una copia manual.

## Panel Administración → Respaldos

| Acción | Protección | Resultado |
| --- | --- | --- |
| Crear | Administración + CSRF | copia consistente y auditada |
| Verificar | Administración + CSRF + nombre interno estricto | integridad SQLite y esquema SGPN mínimo |
| Descargar | Administración + nombre interno estricto | adjunto `no-store`, evento auditado |
| Restaurar | Administración + CSRF + contraseña actual + `RESTAURAR` | copia previa, validación doble, reemplazo atómico, auditoría y cierre de sesión |

No existe carga arbitraria de archivos. Sólo pueden restaurarse copias ya ubicadas en `backups/` cuyo nombre cumpla `pacientes_backup_YYYYMMDD_HHMMSS_microsegundos.db`. Las rutas, nombres con traversal, bases corruptas y archivos SQLite ajenos al esquema se rechazan.

## Lista de comprobación de instalación de la aplicación

1. Descomprime la versión en una carpeta nueva; no mezcles código de versiones distintas.
2. Conserva `instance/` y `backups/`, pero no copies `.venv`, cachés ni archivos temporales.
3. Instala `requirements.txt` y ejecuta `python scripts/build_local_assets.py --check`.
4. Ejecuta `python -m pytest -q`; exige 118 aprobadas. El único `skipped` permitido es el E2E cuando Chromium no está instalado.
5. Inicia sesión como Administración y abre **Administración → Respaldos**.
6. Crea una copia, pulsa **Verificar** y descarga una copia de prueba.
7. En una base de demostración, modifica un dato, restaura una copia anterior y confirma que la sesión se cierre y el dato vuelva a su estado anterior.
8. Revisa **Auditoría** para comprobar `CREAR_RESPALDO`, `VERIFICAR_RESPALDO`, `DESCARGAR_RESPALDO` y `RESTAURAR_RESPALDO`.
9. No uses datos reales si la creación/verificación/restauración de prueba falla.

## Pruebas positivas y negativas

`tests/test_continuity_security.py` cubre recursos/CSP, base válida y corrupta, restauración atómica, respaldo tras éxito, ausencia de copia tras rechazo, falla de almacenamiento, roles, CSRF, creación, verificación, descarga, nombre inválido, contraseña/frase incorrectas, copia corrupta y restauración correcta. `tests/e2e/test_browser_security.py` abre un servidor temporal y valida login, mismo origen, consola CSP y confirmación local con Chromium.

## Estatus mínimo de seguridad

En el alcance de una aplicación local controlada, 1.10.1 cumple el mínimo técnico definido: autenticación individual, roles de servidor, CSRF, validación autoritativa, bloqueo de acceso, sesiones revocables, auditoría, recursos autocontenidos, CSP estricta, copias consistentes y restauración probada. Este resultado no sustituye una prueba de penetración, evaluación de privacidad, cifrado en reposo ni controles necesarios para una publicación en red.

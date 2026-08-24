# Recuperación segura de acceso

La aplicación no envía enlaces ni contraseñas por correo. Es una decisión deliberada: la versión local no dispone de un proveedor de correo, verificación de dominio ni segundo factor confiable. Simular “olvidé mi contraseña” con preguntas de seguridad o respuestas almacenadas reduciría la protección.

## Escenarios

### El usuario conoce su contraseña

En el menú de cuenta selecciona **Cambiar contraseña**. Debe capturar la actual y una nueva de 12–128 caracteres con mayúscula, minúscula, número y símbolo. La nueva no puede contener el usuario/correo ni ser igual a la anterior. Al guardar, `auth_version` aumenta y las demás sesiones dejan de ser válidas.

### El usuario la olvidó y existe otro administrador

1. El administrador abre **Gestión de usuarios**.
2. Selecciona **Restablecer** junto a la cuenta.
3. Confirma su propia contraseña; después de cinco fallos la acción se bloquea en esa sesión.
4. El sistema genera una contraseña temporal criptográfica y la muestra una sola vez.
5. El administrador la entrega directamente al usuario. No debe copiarla en la bitácora, notas clínicas o mensajería no autorizada.
6. Las sesiones anteriores del usuario quedan invalidadas. Al iniciar, sólo puede abrir **Cambiar contraseña** hasta definir una credencial definitiva.

La contraseña temporal se guarda únicamente como hash Scrypt. Los logs y la auditoría registran IDs, resultado e invalidación de sesiones, nunca el valor.

### Nadie puede acceder como administrador

La persona autorizada debe tener acceso al mismo equipo y a la carpeta de datos. Cierra el servidor y ejecuta desde la raíz:

```powershell
python run.py --reset-password NOMBRE_USUARIO
```

Con PyInstaller:

```powershell
SistemaPacientes.exe --reset-password NOMBRE_USUARIO
```

El comando solicita dos veces una contraseña de recuperación sin mostrarla en pantalla. Sólo acepta una cuenta con rol administrador, reactiva la cuenta, elimina bloqueos, invalida sesiones y obliga a reemplazar esa contraseña en el siguiente login. No abre el navegador ni inicia Waitress.

## Límites y operación

- El acceso al equipo y a `instance/pacientes.db` es parte de la frontera de seguridad. Protege la cuenta de Windows, el disco y los respaldos.
- No compartas la contraseña temporal en correo personal, WhatsApp abierto o capturas de pantalla.
- Si se sospecha acceso no autorizado al equipo, cambia todas las credenciales y revisa **Auditoría** antes de continuar.
- Para un futuro despliegue en red debe implementarse recuperación por token de un solo uso, expiración, proveedor transaccional verificado y segundo factor; el flujo local no debe exponerse por Internet.

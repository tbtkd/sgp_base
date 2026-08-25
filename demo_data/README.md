# Datos de demostración

Este directorio contiene recursos ficticios para validar SMBase. Ningún dato corresponde a una persona real y nada se carga durante el arranque de la aplicación.

## Carga recomendada

1. Haz una copia de `instance/pacientes.db` o utiliza una instalación de pruebas.
2. Con el entorno virtual activo ejecuta:

   ```powershell
   python seed_demo.py --confirm
   ```

3. El comando crea cuentas de Administración, Medicina general, Odontología, Nutrición y Recepción; seis pacientes, historiales, nueve consultas, siete citas, dieciocho pagos operativos y una receta de tres medicamentos.
4. La contraseña aleatoria de las cuentas nuevas se muestra una sola vez en la consola. También puede definirse antes de ejecutar mediante `SGPN_DEMO_PASSWORD`.
5. Para validar la importación inicia sesión como `demo_nutricion` y carga `demo_data/expediente_antropometrico_demo.xlsx` desde el detalle de un paciente. Medicina general, Odontología y Recepción no deben ver esa opción.

Los dieciocho pagos cubren los cuatro métodos, todos los estados, varios periodos, responsables distintos, vínculos con citas de diferentes estados y un cobro deliberadamente sin cita relacionada aunque el paciente sí tenga una programada. También existen casos para cancelación, búsqueda por nombre completo, CSV neutralizado y migración que requiere revisión. Consulta [ESCENARIOS_PAGOS_1_10.md](ESCENARIOS_PAGOS_1_10.md) para la matriz de validación. El conjunto es idempotente, no representa ingresos reales y no genera CFDI.

Las cuentas y registros demostrativos deben desactivarse o descartarse antes de trabajar con información clínica real.

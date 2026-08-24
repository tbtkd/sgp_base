# Documento de Requerimientos
Sistema de Gestión de Pacientes Nutriológicos (SGPN)

## 1. Introducción
### 1.1 Propósito
El Sistema de Gestión de Pacientes Nutriológicos (SGPN) tiene como objetivo facilitar el seguimiento y control de pacientes en una clínica nutricional, permitiendo el registro de valoraciones antropométricas, historiales clínicos y control de pagos.

### 1.2 Alcance
El sistema abarca la gestión completa de pacientes, desde su registro inicial hasta el seguimiento de sus valoraciones antropométricas y pagos.

## 2. Casos de Uso

### UC-01: Gestión de Pacientes
**Actor Principal:** Nutriólogo
**Descripción:** Permite administrar la información de los pacientes.

**Flujo Principal:**
1. Registrar nuevo paciente
   - Datos requeridos:
     * Nombre (obligatorio)
     * Apellido Paterno (obligatorio)
     * Apellido Materno (obligatorio)
     * Fecha de nacimiento (obligatorio)
     * Teléfono (obligatorio, 10 dígitos)
     * Correo (obligatorio, único)
     * Ciudad (obligatorio)

2. Consultar pacientes
   - Búsqueda por:
     * Nombre
     * Apellidos
   - Mostrar estado de pago

3. Editar información del paciente
4. Cambiar estado del paciente (activo/inactivo)

### UC-02: Gestión de Historial Clínico
**Actor Principal:** Nutriólogo
**Descripción:** Registro y consulta del historial clínico del paciente.

**Flujo Principal:**
1. Registrar historial clínico
   - Información requerida:
     * Cirugías
     * Padecimientos
     * Medicamentos
     * Suplementos
     * Enfermedades previas/actuales
     * Actividad física
     * Hábitos alimenticios

2. Consultar historial clínico
3. Actualizar información del historial

### UC-03: Gestión de Valoraciones Antropométricas
**Actor Principal:** Nutriólogo
**Descripción:** Control de medidas y valoraciones del paciente.

**Flujo Principal:**
1. Registrar nueva valoración
   - Datos requeridos:
     * Número de cita (auto-incrementable)
     * Fecha
     * Medidas corporales:
       - Estatura
       - Peso
       - IMC (calculado)
       - % Grasa
       - Medidas (cintura, tórax, etc.)
     * Signos vitales:
       - Tensión arterial
       - Frecuencia cardíaca
     * Pliegues cutáneos
     * Última dieta

2. Consultar valoraciones anteriores
3. Registrar última dieta

### UC-04: Gestión de Pagos
**Actor Principal:** Nutriólogo
**Descripción:** Control de pagos de los pacientes.

**Flujo Principal:**
1. Registrar pago
   - Fecha de pago
2. Consultar último pago
3. Verificar estado de pago

### UC-05: Importación de Datos
**Actor Principal:** Nutriólogo
**Descripción:** Importación masiva de valoraciones desde Excel.

**Flujo Principal:**
1. Cargar archivo Excel
   - Validaciones:
     * Formato .xls o .xlsx
     * Estructura específica de columnas
2. Validar datos
3. Importar registros
4. Mostrar resultado de importación

## 3. Reglas de Negocio

### RN-01: Registro de Pacientes
- El correo electrónico debe ser único
- El teléfono debe tener exactamente 10 dígitos
- La fecha de nacimiento no puede ser futura

### RN-02: Valoraciones
- El número de cita se auto-incrementa
- No se pueden duplicar valoraciones para la misma fecha
- El IMC se calcula automáticamente

### RN-03: Importación Excel
- No se permiten registros duplicados
- Se valida la estructura del archivo
- Se mantiene registro de errores en la importación

### RN-04: Pagos
- Se debe registrar la fecha de cada pago
- Solo se permite un pago por fecha

## 4. Requerimientos No Funcionales

### RNF-01: Rendimiento
- Tiempo de respuesta máximo de 3 segundos
- Soporte para múltiples usuarios concurrentes

### RNF-02: Seguridad
- Validación de datos en frontend y backend
- Protección contra inyección SQL
- Sanitización de entradas de usuario

### RNF-03: Usabilidad
- Interfaz responsiva
- Mensajes de error claros
- Navegación intuitiva

### RNF-04: Mantenibilidad
- Código modular y documentado
- Logs para desarrollo
- Configuración separada para desarrollo y producción 
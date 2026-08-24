-- Tabla de Usuarios y Seguridad
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'medico' CHECK (rol IN ('admin', 'medico', 'recepcion')),
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Pacientes (General)
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido_paterno TEXT NOT NULL,
    apellido_materno TEXT NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    genero TEXT DEFAULT 'No especificado',
    telefono TEXT NOT NULL,
    correo TEXT UNIQUE NOT NULL,
    ciudad TEXT NOT NULL,
    direccion TEXT,
    ocupacion TEXT,
    contacto_emergencia TEXT,
    telefono_emergencia TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'activo' CHECK (status IN ('activo', 'inactivo'))
);

-- Tabla de Historial Clínico General
CREATE TABLE IF NOT EXISTS historial_clinico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    antecedentes_heredofamiliares TEXT,
    antecedentes_patologicos TEXT,
    antecedentes_no_patologicos TEXT,
    alergias TEXT,
    cirugias TEXT,
    padecimientos TEXT,
    medicamentos TEXT,
    suplementos TEXT,
    enfermedades_previas TEXT,
    enfermedades_actuales TEXT,
    tipo_actividad_fisica TEXT,
    frecuencia_actividad_fisica TEXT,
    tiempo_actividad_fisica TEXT,
    numero_comidas_diarias INTEGER,
    alimentos_normales TEXT,
    alimentos_no_gustados TEXT,
    motivo_consulta_frecuente TEXT,
    observaciones_generales TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
);

-- Tabla de Consultas Clínicas / Signos Vitales / Valoraciones
CREATE TABLE IF NOT EXISTS valoracion_antropometrica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    numero_cita INTEGER NOT NULL,
    fecha DATE NOT NULL,
    motivo_consulta TEXT,
    sintomas TEXT,
    -- Signos vitales generales
    tension_arterial TEXT,
    frecuencia_cardiaca INTEGER,
    frecuencia_respiratoria INTEGER,
    temperatura FLOAT,
    saturacion_oxigeno INTEGER,
    -- Somatometría básica
    estatura FLOAT,
    peso FLOAT,
    imc FLOAT,
    -- Diagnóstico y tratamiento clínico general
    diagnostico TEXT,
    plan_tratamiento TEXT,
    receta_indicaciones TEXT,
    -- Medidas antropométricas adicionales (opcionales)
    grasa FLOAT,
    cintura FLOAT,
    torax FLOAT,
    brazo FLOAT,
    cadera FLOAT,
    pierna FLOAT,
    pantorrilla FLOAT,
    bicep FLOAT,
    tricep FLOAT,
    suprailiaco FLOAT,
    subescapular FLOAT,
    femoral FLOAT,
    porcentaje_grasa TEXT,
    ultima_dieta TEXT,
    proxima_cita DATE,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
);

-- Tabla de Citas
CREATE TABLE IF NOT EXISTS citas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    motivo TEXT,
    estado TEXT DEFAULT 'pendiente',
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
);

-- Tabla de Pagos
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    fecha_pago DATE NOT NULL,
    monto FLOAT DEFAULT 0.0,
    concepto TEXT DEFAULT 'Consulta general',
    metodo_pago TEXT DEFAULT 'Efectivo',
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
);

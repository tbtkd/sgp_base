def safe_float(val, default=0.0):
    if val is None or str(val).strip() == "":
        return default
    try:
        return float(val)
    except ValueError:
        return default

def safe_int(val, default=0):
    if val is None or str(val).strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default

def validar_campos(form, campos_requeridos):
    """
    Valida que los campos requeridos estén presentes y no vacíos en el formulario.
    Retorna una lista de mensajes de error.
    """
    errores = []
    for campo in campos_requeridos:
        if not form.get(campo) or str(form.get(campo)).strip() == "":
            errores.append(f"El campo '{campo.replace('_', ' ').capitalize()}' es obligatorio.")
    return errores

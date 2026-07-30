document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("formPaciente")
  if (form) {
    form.addEventListener("submit", (event) => {
      if (!validarFormulario()) {
        event.preventDefault()
      }
    })
  }document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("formPaciente")
    if (form) {
      form.addEventListener("submit", (event) => {
        if (!validarFormulario()) {
          event.preventDefault()
        }
      })
    }
  })
  
  function validarFormulario() {
    const nombre = document.getElementById("nombre").value.trim()
    const apellidoPaterno = document.getElementById("apellido_paterno").value.trim()
    const apellidoMaterno = document.getElementById("apellido_materno").value.trim()
    const fechaNacimiento = document.getElementById("fecha_nacimiento").value
    const telefono = document.getElementById("telefono").value.trim()
    const correo = document.getElementById("correo").value.trim()
    const ciudad = document.getElementById("ciudad").value.trim()
  
    if (
      nombre === "" ||
      apellidoPaterno === "" ||
      apellidoMaterno === "" ||
      fechaNacimiento === "" ||
      telefono === "" ||
      correo === "" ||
      ciudad === ""
    ) {
      alert("Por favor, complete todos los campos.")
      return false
    }
  
    if (!validarFechaNacimiento(fechaNacimiento)) {
      alert("La fecha de nacimiento no es válida.")
      return false
    }
  
    if (!validarTelefono(telefono)) {
      alert("El número de teléfono no es válido. Debe contener solo números y tener 10 dígitos.")
      return false
    }
  
    if (!validarCorreo(correo)) {
      alert("El correo electrónico no es válido.")
      return false
    }
  
    return true
  }
  
  function validarFechaNacimiento(fecha) {
    const hoy = new Date()
    const fechaNacimiento = new Date(fecha)
    return fechaNacimiento < hoy
  }
  
  function validarTelefono(telefono) {
    const regex = /^\d{10}$/
    return regex.test(telefono)
  }
  
  function validarCorreo(correo) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return regex.test(correo)
  }
  
  
})

function validarFormulario() {
  const nombre = document.getElementById("nombre").value.trim()
  const apellidoPaterno = document.getElementById("apellido_paterno").value.trim()
  const apellidoMaterno = document.getElementById("apellido_materno").value.trim()
  const fechaNacimiento = document.getElementById("fecha_nacimiento").value
  const telefono = document.getElementById("telefono").value.trim()
  const correo = document.getElementById("correo").value.trim()
  const ciudad = document.getElementById("ciudad").value.trim()

  if (
    nombre === "" ||
    apellidoPaterno === "" ||
    apellidoMaterno === "" ||
    fechaNacimiento === "" ||
    telefono === "" ||
    correo === "" ||
    ciudad === ""
  ) {
    alert("Por favor, complete todos los campos.")
    return false
  }

  if (!validarFechaNacimiento(fechaNacimiento)) {
    alert("La fecha de nacimiento no es válida.")
    return false
  }

  if (!validarTelefono(telefono)) {
    alert("El número de teléfono no es válido. Debe contener solo números y tener 10 dígitos.")
    return false
  }

  if (!validarCorreo(correo)) {
    alert("El correo electrónico no es válido.")
    return false
  }

  return true
}

function validarFechaNacimiento(fecha) {
  const hoy = new Date()
  const fechaNacimiento = new Date(fecha)
  return fechaNacimiento < hoy
}

function validarTelefono(telefono) {
  const regex = /^\d{10}$/
  return regex.test(telefono)
}

function validarCorreo(correo) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return regex.test(correo)
}


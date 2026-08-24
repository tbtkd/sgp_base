formCargarExcel.addEventListener('submit', function(e) {
    e.preventDefault();
    const submitButton = this.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando...';
    
    const formData = new FormData(this);
    
    fetch(`/pacientes/${pacienteId}/cargar-excel`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Archivo cargado exitosamente');
            window.location.reload();
        } else {
            alert('Error al cargar el archivo: ' + data.message);
        }
    })
    .catch(error => {
        alert('Error al cargar el archivo: ' + error);
    })
    .finally(() => {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-upload"></i> Cargar';
    });
}); 
document.addEventListener('DOMContentLoaded', function() {
    const formCargarExcel = document.getElementById('formCargarExcel') || document.querySelector('.excel-upload-form') || document.querySelector('form[enctype="multipart/form-data"]');
    
    if (!formCargarExcel) return;

    formCargarExcel.addEventListener('submit', function(e) {
        e.preventDefault();

        const fileInput = this.querySelector('input[type="file"]');
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            if (typeof mostrarModalError === 'function') {
                mostrarModalError("Por favor, selecciona un archivo Excel antes de continuar.");
            } else {
                alert("Por favor, selecciona un archivo Excel antes de continuar.");
            }
            return;
        }

        const submitButton = this.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.dataset.originalHtml = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando...';
        }

        const formData = new FormData(this);
        const actionUrl = this.action || window.location.href;

        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                return response.json();
            } else {
                return response.text().then(text => {
                    throw new Error("Respuesta no válida del servidor (no es JSON)");
                });
            }
        })
        .then(data => {
            if (data.success) {
                const successMsg = data.message || "Archivo procesado correctamente";
                if (typeof mostrarModalExito === 'function') {
                    mostrarModalExito(successMsg);
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    alert(successMsg);
                    window.location.reload();
                }
            } else {
                const errorMsg = data.message || "Ocurrió un error al cargar el archivo";
                if (typeof mostrarModalError === 'function') {
                    mostrarModalError(errorMsg);
                } else {
                    alert(errorMsg);
                }
            }
        })
        .catch(error => {
            console.error("Error al subir archivo:", error);
            const errorMsg = "Ocurrió un error inesperado al procesar la solicitud.";
            if (typeof mostrarModalError === 'function') {
                mostrarModalError(errorMsg);
            } else {
                alert(errorMsg);
            }
        })
        .finally(() => {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.dataset.originalHtml || '<i class="fas fa-upload"></i> Cargar';
            }
        });
    });
});

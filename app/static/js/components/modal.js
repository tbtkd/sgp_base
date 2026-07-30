export function initModal() {
    const modal = document.getElementById('modalCargarExcel');
    if (!modal) return;  // Si no existe el modal, salimos
    
    const closeBtn = modal.querySelector('.modal-upload__close');
    if (!closeBtn) return;  // Si no existe el botón de cerrar, salimos
    
    // Función para abrir el modal
    window.openExcelModal = function() {
        modal.style.display = 'flex';
    };

    // Función para cerrar el modal
    function closeModal() {
        modal.style.display = 'none';
    }

    // Eventos para cerrar el modal
    closeBtn.addEventListener('click', closeModal);
    
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });
} 
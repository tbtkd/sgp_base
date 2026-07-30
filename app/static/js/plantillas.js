/**
 * plantillas.js - Lógica de gestión y activación de plantillas de WhatsApp
 */

function mostrarToast(mensaje, tipo = 'success') {
    let toast = document.getElementById('appToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'appToast';
        toast.className = 'fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border text-sm font-medium transition-all duration-300 transform translate-y-20 opacity-0';
        document.body.appendChild(toast);
    }
    
    toast.className = 'fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border bg-gray-900 text-white border-gray-800 transition-all duration-300 transform translate-y-20 opacity-0';
    toast.innerHTML = `<div class="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0"><i class="fas fa-check"></i></div><span>${mensaje}</span>`;

    setTimeout(() => {
        toast.classList.remove('translate-y-20', 'opacity-0');
    }, 10);

    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 3000);
}

function activarPlantilla(id) {
    fetch(`/plantillas-mensajes/activar/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarToast(data.message);
        } else {
            alert('Error al activar la plantilla.');
        }
    })
    .catch(err => {
        console.error('Error:', err);
        alert('Error de red.');
    });
}

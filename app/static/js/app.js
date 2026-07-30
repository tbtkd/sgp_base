document.addEventListener('DOMContentLoaded', () => {
    // Auto-cierre de alertas flash después de 5 segundos
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

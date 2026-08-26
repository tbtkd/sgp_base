(function initializeUserManagement() {
    'use strict';
    const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const activeCounter = document.getElementById('contadorUsuariosActivos');
    const inactiveCounter = document.getElementById('contadorUsuariosInactivos');

    async function changeStatus(button) {
        const disabling = button.classList.contains('is-activo');
        const result = await window.confirmarAccion({
            titulo: disabling ? '¿Inhabilitar esta cuenta?' : '¿Habilitar esta cuenta?',
            mensaje: disabling ? 'La persona ya no podrá entrar al sistema hasta que vuelvas a habilitar su cuenta.' : 'La persona podrá volver a iniciar sesión con su contraseña actual.',
            textoConfirmar: disabling ? 'Sí, inhabilitar' : 'Sí, habilitar',
            textoCancelar: 'Cancelar', icono: 'question',
        });
        if (!result.isConfirmed) return;
        button.disabled = true;
        try {
            const response = await fetch(`/usuarios/${button.dataset.userStatus}/cambiar-estatus`, { method: 'POST', headers: { 'X-CSRFToken': token, 'X-Requested-With': 'XMLHttpRequest' } });
            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.error || 'No se pudo cambiar el acceso.');
            const active = data.nuevo_estado === 'activo';
            const badge = document.getElementById(`status-badge-${button.dataset.userStatus}`);
            badge.className = `user-status-badge is-${data.nuevo_estado}`;
            badge.textContent = active ? 'Con acceso' : 'Sin acceso';
            button.className = active ? 'is-activo' : 'is-inactivo';
            button.textContent = active ? 'Inhabilitar' : 'Habilitar';
            if (activeCounter && data.usuarios_activos !== undefined) activeCounter.textContent = data.usuarios_activos;
            if (inactiveCounter && data.usuarios_activos !== undefined) inactiveCounter.textContent = Number(document.getElementById('contadorUsuariosTotal')?.textContent || 0) - Number(data.usuarios_activos);
        } catch (error) {
            await window.mostrarAlerta('No se cambió el acceso', error.message || 'Inténtalo nuevamente.', 'error');
        } finally { button.disabled = false; }
    }
    document.querySelectorAll('[data-user-status]').forEach((button) => button.addEventListener('click', () => changeStatus(button)));
}());

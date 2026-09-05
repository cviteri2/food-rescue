document.addEventListener('DOMContentLoaded', () => {
  const badge = document.getElementById('notif-badge');
  if (!badge) return;

  async function revisarNotificaciones() {
    try {
      const notificaciones = await apiFetch('/api/notificaciones');
      if (notificaciones.length > 0) {
        badge.textContent = notificaciones.length;
        badge.hidden = false;
      } else {
        badge.hidden = true;
      }
    } catch (err) {
      // Silencioso: un fallo de polling no debe interrumpir la sesion del usuario.
    }
  }

  revisarNotificaciones();
  setInterval(revisarNotificaciones, 18000);
});

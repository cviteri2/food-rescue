document.addEventListener('DOMContentLoaded', () => {
  const mapa = L.map('mapa-organizacion').setView([ORG_LAT, ORG_LNG], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(mapa);

  L.marker([ORG_LAT, ORG_LNG]).addTo(mapa).bindPopup('Tu organizacion').openPopup();

  let marcadores = [];

  async function reclamar(id) {
    try {
      await apiFetch(`/api/publicaciones/${id}/reclamar`, { method: 'POST' });
      await cargarPublicaciones();
    } catch (err) {
      alert(err.message);
    }
  }
  window.reclamarPublicacion = reclamar;

  async function cargarPublicaciones() {
    let publicaciones;
    try {
      publicaciones = await apiFetch('/api/publicaciones-cercanas');
    } catch (err) {
      return;
    }

    marcadores.forEach((m) => mapa.removeLayer(m));
    marcadores = [];

    const lista = document.getElementById('lista-publicaciones');
    lista.innerHTML = '';

    if (publicaciones.length === 0) {
      lista.innerHTML = '<li>No hay publicaciones disponibles cerca de ti por ahora.</li>';
      return;
    }

    publicaciones.forEach((p) => {
      const marcador = L.marker([p.lat, p.lng]).addTo(mapa);
      marcador.bindPopup(
        `<strong>${p.titulo}</strong><br>${p.cantidad || ''}<br>${p.distancia_km} km<br>` +
          `<button onclick="reclamarPublicacion(${p.id})">Reclamar</button>`
      );
      marcadores.push(marcador);

      const li = document.createElement('li');
      li.innerHTML =
        `<strong>${p.titulo}</strong> (${p.comercio_nombre}) - ${p.distancia_km} km - ` +
        `expira ${new Date(p.expira_en).toLocaleString()} ` +
        `<button onclick="reclamarPublicacion(${p.id})">Reclamar</button>`;
      lista.appendChild(li);
    });
  }

  cargarPublicaciones();
  setInterval(cargarPublicaciones, 20000);
});

function initMapaSeleccion(mapId, latInputId, lngInputId, latInicial, lngInicial) {
  const mapa = L.map(mapId).setView([latInicial, lngInicial], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(mapa);

  let marcador = null;

  function colocarMarcador(lat, lng) {
    if (marcador) {
      marcador.setLatLng([lat, lng]);
    } else {
      marcador = L.marker([lat, lng], { draggable: true }).addTo(mapa);
      marcador.on('dragend', () => {
        const pos = marcador.getLatLng();
        document.getElementById(latInputId).value = pos.lat;
        document.getElementById(lngInputId).value = pos.lng;
      });
    }
    document.getElementById(latInputId).value = lat;
    document.getElementById(lngInputId).value = lng;
  }

  mapa.on('click', (e) => colocarMarcador(e.latlng.lat, e.latlng.lng));

  return mapa;
}

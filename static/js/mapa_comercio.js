function resizeImagen(file, maxAncho = 800, calidad = 0.7) {
  return new Promise((resolve, reject) => {
    const lector = new FileReader();
    lector.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const escala = Math.min(1, maxAncho / img.width);
        const canvas = document.createElement('canvas');
        canvas.width = img.width * escala;
        canvas.height = img.height * escala;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => resolve(blob), 'image/jpeg', calidad);
      };
      img.onerror = reject;
      img.src = e.target.result;
    };
    lector.onerror = reject;
    lector.readAsDataURL(file);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('form-publicacion');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const mensaje = document.getElementById('mensaje-publicacion');
    mensaje.hidden = true;

    const formData = new FormData(form);
    const inputFoto = document.getElementById('input-foto');
    formData.delete('foto');

    if (inputFoto.files.length > 0) {
      const blob = await resizeImagen(inputFoto.files[0]);
      formData.append('foto', blob, 'foto.jpg');
    }

    try {
      await apiFetch('/api/publicaciones', { method: 'POST', body: formData });
      window.location.reload();
    } catch (err) {
      mensaje.textContent = err.message;
      mensaje.hidden = false;
    }
  });

  document.querySelectorAll('.btn-entregar').forEach((btn) => {
    btn.addEventListener('click', async () => {
      try {
        await apiFetch(`/api/publicaciones/${btn.dataset.id}/entregar`, { method: 'POST' });
        window.location.reload();
      } catch (err) {
        alert(err.message);
      }
    });
  });
});

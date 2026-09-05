async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  let data = null;
  try {
    data = await response.json();
  } catch (e) {
    data = null;
  }
  if (!response.ok) {
    const mensaje = (data && data.error) || `Error ${response.status}`;
    throw new Error(mensaje);
  }
  return data;
}

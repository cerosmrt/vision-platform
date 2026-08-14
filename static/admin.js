// Wrapper único de fetch para el admin: inyecta CSRF, manda JSON y avisa en error.
// Devuelve el JSON de la respuesta, o null si algo falló.

const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';

async function api(url, { method = 'GET', body = null } = {}) {
  const opciones = {
    method,
    headers: { 'X-CSRFToken': CSRF },
  };
  if (body !== null) {
    opciones.headers['Content-Type'] = 'application/json';
    opciones.body = JSON.stringify(body);
  }

  let resp;
  try {
    resp = await fetch(url, opciones);
  } catch {
    alert('Sin conexión con el servidor.');
    return null;
  }

  if (resp.status === 401) {
    location.href = '/admin/login';
    return null;
  }
  if (!resp.ok) {
    const datos = await resp.json().catch(() => ({}));
    alert(datos.error || 'No se pudo completar la operación.');
    return null;
  }
  return resp.json().catch(() => ({}));
}

// Escapa HTML antes de meterlo en el DOM desde JS.
function esc(texto) {
  const div = document.createElement('div');
  div.textContent = texto ?? '';
  return div.innerHTML;
}

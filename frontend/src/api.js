const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
};

const csrftoken = () => getCookie('csrftoken');

export async function apiFetch(path, { method = 'GET', body, headers } = {}) {
  const opts = {
    method,
    headers: {
      'Accept': 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
    // klíčové: session cookies do requestu
    credentials: 'include',
  };

  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
    opts.headers['X-CSRFToken'] = csrftoken();
  }

  if (body) {
    opts.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  const res = await fetch(path, opts);

  // přesměrování na login (Django vrátí HTML) – ošetřeno
  const contentType = res.headers.get('content-type') || '';
  if (!res.ok) {
    // Zkus JSON, když ne, vyhoď text
    if (contentType.includes('application/json')) {
      const data = await res.json();
      throw { status: res.status, data };
    } else {
      const text = await res.text();
      throw { status: res.status, data: { detail: text } };
    }
  }

  if (contentType.includes('application/json')) {
    return await res.json();
  }
  return await res.text();
}
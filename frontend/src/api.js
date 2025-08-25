const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
};

const csrftoken = () => getCookie('csrftoken');

export async function ensureCsrf() {
  // If we already have a csrftoken cookie, nothing to do
  if (csrftoken()) return csrftoken();
  // Hit Django endpoint that sets the CSRF cookie
  await fetch('/api/csrf/', { credentials: 'include' });
  return csrftoken();
}

export async function apiFetch(path, { method = 'GET', body, headers, _retry = false } = {}) {
  const opts = {
    method,
    headers: {
      'Accept': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
    // klíčové: session cookies do requestu
    credentials: 'include',
  };

  const upper = method.toUpperCase();

  // U mutujících metod zajistíme CSRF cookie a přidáme hlavičku
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(upper)) {
    if (!csrftoken()) {
      await ensureCsrf();
    }
    opts.headers['X-CSRFToken'] = csrftoken();
  }

  if (body) {
    opts.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  const res = await fetch(path, opts);
  const contentType = res.headers.get('content-type') || '';

  // Pokud CSRF selže (403), jednou zkusíme obnovit CSRF a retrynout
  if (res.status === 403 && !_retry) {
    await ensureCsrf();
    // Aktualizujeme CSRF hlavičku a retry
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(upper)) {
      opts.headers['X-CSRFToken'] = csrftoken();
    }
    const retryRes = await fetch(path, opts);
    return handleResponse(retryRes);
  }

  return handleResponse(res);
}

async function handleResponse(res) {
  if (res.status === 204) return null;

  const contentType = res.headers.get('content-type') || '';

  if (!res.ok) {
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

export const api = {
  csrf: ensureCsrf,
  signup: (payload) => apiFetch('/api/signup/', { method: 'POST', body: payload }),
  login: (payload) => apiFetch('/api/login/', { method: 'POST', body: payload }),
  logout: () => apiFetch('/api/logout/', { method: 'POST' }),
  me: () => apiFetch('/api/me/'),
};
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

// API base (can be overridden by REACT_APP_API_BASE)
const API_BASE = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8000';

// Read CSRF token from cookies (for Django session-auth)
function getCSRFToken() {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

// Helper: build headers incl. auth token & CSRF if present
function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('authToken');
  if (token) {
    // If you use DRF TokenAuth -> `Token ${token}`; if JWT -> `Bearer ${token}`
    headers['Authorization'] = `Token ${token}`;
  }
  const csrf = getCSRFToken();
  if (csrf) {
    headers['X-CSRFToken'] = csrf;
  }
  return headers;
}

function NewEvent() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    navigate('/login');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/events/`, {
        method: 'POST',
        credentials: 'include',        // send cookies for session auth
        mode: 'cors',
        headers: getAuthHeaders(),
        body: JSON.stringify({ title, description })
      });

      if (res.status === 401) {
        // not authenticated 
        navigate('/login');
        return;
      }

      if (!res.ok) {
        let message = 'Chyba při vytváření eventu';
        try {
          const dataErr = await res.json();
          message = typeof dataErr === 'string' ? dataErr : JSON.stringify(dataErr);
        } catch (e) {
          const txt = await res.text();
          if (txt) message = txt;
        }
        throw new Error(message);
      }

      const data = await res.json();
      navigate(`/events/${data.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '48px auto 80px', padding: 24, background: '#fff', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.06)', fontFamily: 'Poppins, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif' }}>
      {/* mini top bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#1e3a8a' }}>Nový event</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {localStorage.getItem('authToken') ? (
            <button onClick={handleLogout} style={{ padding: '6px 12px', background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: 10, cursor: 'pointer', fontWeight: 600, color: '#1e3a8a' }}>Odhlásit</button>
          ) : (
            <>
              <Link to="/login" style={{ textDecoration: 'none', fontWeight: 600, color: '#2563eb' }}>Přihlásit</Link>
              <Link to="/signup" style={{ textDecoration: 'none', fontWeight: 600, color: '#2563eb' }}>Registrovat</Link>
            </>
          )}
        </div>
      </div>

      {error && (
        <div style={{ background: '#fee2e2', border: '1px solid #fecaca', color: '#991b1b', padding: '10px 12px', borderRadius: 8, marginBottom: 12 }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', fontWeight: 600, marginBottom: 6 }}>Název</label>
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            required
            style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: 10 }}
            placeholder="Např. Chorvatsko 2025"
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', fontWeight: 600, marginBottom: 6 }}>Popis</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={4}
            style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: 10 }}
            placeholder="Krátký popis akce…"
          />
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit" disabled={loading} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 16px', background: '#2563eb', border: '1px solid #1f4ed8', color: '#fff', borderRadius: 10, fontWeight: 600, cursor: 'pointer', boxShadow: '0 6px 16px rgba(37,99,235,0.25)' }}>
            {loading ? 'Vytvářím…' : 'Vytvořit'}
          </button>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 16px', background: '#f8fafc', border: '1px solid #e2e8f0', color: '#334155', borderRadius: 10, fontWeight: 600, textDecoration: 'none' }}>Zpět</Link>
        </div>
      </form>
    </div>
  );
}

export default NewEvent;
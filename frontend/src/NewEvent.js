import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function NewEvent() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    fetch('/api/events/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ title, description })
    })
    .then(res => {
      if (!res.ok) throw new Error('Chyba při vytváření eventu');
      return res.json();
    })
    .then(data => {
      navigate(`/events/${data.id}`); // přesměruj na detail nového eventu
    })
    .catch(err => setError(err.message));
  };

  return (
    <div>
      <h2>Nový event</h2>
      {error && <p style={{color:'red'}}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label>Název:</label><br />
          <input type="text" value={title} onChange={e => setTitle(e.target.value)} required />
        </div>
        <div>
          <label>Popis:</label><br />
          <textarea value={description} onChange={e => setDescription(e.target.value)} />
        </div>
        <button type="submit">Vytvořit</button>
      </form>
    </div>
  );
}

export default NewEvent;
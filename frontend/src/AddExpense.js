import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

function AddExpense() {
  const { id } = useParams(); // event ID
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [paidBy, setPaidBy] = useState('');
  const [participants, setParticipants] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`/api/events/${id}/`)
      .then(res => res.json())
      .then(data => setParticipants(data.participants || []));
  }, [id]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    fetch('/api/expenses/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        description,
        amount: parseFloat(amount),
        paid_by: paidBy,
        event: Number(id), // convert id to number
      }),
    })
      .then(res => {
        if (!res.ok) {
          return res.json().then(err => { throw new Error(JSON.stringify(err)); });
        }
        return res.json();
      })
      .then(() => {
        setDescription('');
        setAmount('');
        setPaidBy('');
        navigate(`/events/${id}`);
      })
      .catch(err => setError(err.message));
  };

  return (
    <div>
      <h2>Přidat výdaj</h2>
      {error && <p style={{color: 'red'}}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label>Popis:</label><br />
          <input
            type="text"
            value={description}
            onChange={e => setDescription(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Částka (Kč):</label><br />
          <input
            type="number"
            step="0.01"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Zaplatil:</label><br />
          <select value={paidBy} onChange={e => setPaidBy(e.target.value)} required>
            <option value="">Vyber účastníka</option>
            {participants.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
        <button type="submit">Přidat výdaj</button>
      </form>
    </div>
  );
}

export default AddExpense;
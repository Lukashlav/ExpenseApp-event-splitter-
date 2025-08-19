import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

function AddExpense() {
  const { id } = useParams(); // event ID
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [paidBy, setPaidBy] = useState('');
  const [participants, setParticipants] = useState([]);
  const [selectedParticipants, setSelectedParticipants] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`/api/events/${id}/`)
      .then(res => res.json())
      .then(data => setParticipants(data.participants || []));
  }, [id]);

  const handleCheckboxChange = (participantId) => {
    if (selectedParticipants.includes(participantId)) {
      setSelectedParticipants(selectedParticipants.filter(p => p !== participantId));
    } else {
      setSelectedParticipants([...selectedParticipants, participantId]);
    }
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedParticipants([]);
    } else {
      setSelectedParticipants(participants.map(p => p.id));
    }
    setSelectAll(!selectAll);
  };

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
        event: Number(id),
        split_between_ids: selectedParticipants
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
        setSelectedParticipants([]);
        setSelectAll(false);
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
        <div>
          <label>Přiřadit výdaj:</label><br />
          <div>
            <label>
              <input
                type="checkbox"
                checked={selectAll}
                onChange={handleSelectAll}
              /> Všem účastníkům
            </label>
          </div>
          {participants.map(p => (
            <div key={p.id}>
              <label>
                <input
                  type="checkbox"
                  checked={selectedParticipants.includes(p.id)}
                  onChange={() => handleCheckboxChange(p.id)}
                /> {p.name}
              </label>
            </div>
          ))}
        </div>
        <button type="submit">Přidat výdaj</button>
      </form>
    </div>
  );
}

export default AddExpense;
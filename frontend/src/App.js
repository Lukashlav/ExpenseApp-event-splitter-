import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import EventDetail from './EventDetail';
import NewEvent from './NewEvent';
import AddExpense from './AddExpense';
import './App.css';

function EventList() {
  const [events, setEvents] = React.useState([]);

  React.useEffect(() => {
    fetch('/api/events/')
      .then(res => res.json())
      .then(data => setEvents(data.results || data));
  }, []);

  return (
    <div>
      <h1>Seznam eventů</h1>
      <ul className="event-list">
        {events.map(event => (
          <li key={event.id}>
            <Link to={`/events/${event.id}`}>{event.title}</Link>
          </li>
        ))}
      </ul>
      <Link to="/new-event" className="add-event-link">+ Přidat nový event</Link>
    </div>
  );
}

function App() {
  return (
    <div className="app-container">
      <Routes>
        <Route path="/" element={<EventList />} />
        <Route path="/events/:id" element={<EventDetail />} />
        <Route path="/new-event" element={<NewEvent />} />
        <Route path="/events/:id/add-expense" element={<AddExpense />} />
      </Routes>
    </div>
  );
}

export default App;
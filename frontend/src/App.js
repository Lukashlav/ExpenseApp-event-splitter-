import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import EventDetail from './EventDetail';

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
      <ul>
        {events.map(event => (
          <li key={event.id}>
            <Link to={`/events/${event.id}`}>{event.title}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<EventList />} />
        <Route path="/events/:id" element={<EventDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
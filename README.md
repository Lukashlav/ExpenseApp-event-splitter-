# ExpenseApp-event-splitter-
# ExpenseApp – Event Splitter

ExpenseApp is a full‑stack web application built with **Django + Django REST Framework** (backend) and **React** (frontend).
It allows you to create events, add participants, record expenses and automatically calculate balances and settlement instructions (who owes whom).

## Features
- User authentication with session‑based login, logout, signup (CSRF protected).
- Create and manage events.
- Add participants to events (with or without email, can be updated later).
- Record expenses for an event, assign payer and split between selected participants.
- View per‑participant balances and suggested settlement transactions.
- Categories for expenses.

## Tech Stack
- **Backend:** Django, Django REST Framework, PostgreSQL
- **Frontend:** React (create‑react‑app), fetch API
- **Tests:** pytest + pytest‑django

## Running the application

### Backend (Django)
1. Create and activate virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run database migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the Django development server:
   ```bash
   python manage.py runserver
   ```
   The backend runs on `http://127.0.0.1:8000/`.

### Frontend (React)
1. Open a new terminal.
2. Navigate to the `frontend` directory (where `package.json` is).
3. Install dependencies (first time only):
   ```bash
   npm install
   ```
4. Start React development server:
   ```bash
   npm start
   ```
   The frontend runs on `http://localhost:3000/` and communicates with the Django API.

## How it works
- The frontend fetches data from the Django API (e.g. events, participants, expenses).
- Authentication is handled via Django session cookies + CSRF tokens.
- When you create an event, you can add participants, then record expenses linked to that event.
- Balances and settlement instructions are calculated on the backend and shown in the frontend.

## Running Tests
Tests are written with `pytest`.
Run them with:
```bash
pytest -q
```

---

🚀 With ExpenseApp you can easily split group expenses, track who paid what, and see clear settlement instructions.
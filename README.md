# Learnzo

Adaptive learning platform for mentally challenged children, based on the VARK learning model (Visual, Auditory, Reading/Writing, Kinesthetic).

## Architecture

- **Backend**: FastAPI, SQLAlchemy, MySQL. Layered structure: `app/api` (routers), `app/services`, `app/models`, `app/schemas`, `app/auth`, `app/db`.
- **Frontend**: React 19 + TypeScript + Vite. First page: Register, second: Login. After login: student onboarding (name, age, disability type), VARK questionnaire (20 Yes/No questions), adaptive learning (search by topic), dashboards (student + teacher).
- **Auth**: JWT (Bearer). Roles: `student`, `teacher`. Students have an associated learner profile; teachers have read-only access to all students.

## Backend

### Setup

1. **Choose a database**

   **Option A – SQLite (zero setup, default)**  
   Do nothing. If you don’t set `DATABASE_URL` or any `MYSQL_*` variables, the backend uses a local SQLite file `learnzo.db`.

   **Option B – MySQL** (one of the options below).

   **Option B1 – SQL script (recommended)**  
   From the project root, run as MySQL root:
   ```bash
   mysql -u root -p < scripts/init_mysql.sql
   ```
   This creates database `learnzo`, user `learnzo_user` with password `learnzo_pass`, and grants full access on `learnzo.*`. Tables are created by the app on startup.

   **Option B2 – Manual**  
   In MySQL (as root or admin):
   ```sql
   CREATE DATABASE IF NOT EXISTS learnzo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER IF NOT EXISTS 'learnzo_user'@'localhost' IDENTIFIED BY 'learnzo_pass';
   GRANT ALL PRIVILEGES ON learnzo.* TO 'learnzo_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

   **Option B3 – Use root `config.py` credentials**  
   If you use the repo’s root `config.py` (user `user`, password `aryaanilkumar`), create that user and grant access on `learnzo`, then set env vars so the app uses them: `MYSQL_USER=user`, `MYSQL_PASSWORD=aryaanilkumar`, `MYSQL_DB=learnzo`.

2. **Environment variables** (optional; loaded from `.env` if present):
   - `DATABASE_URL` (recommended; overrides everything)
   - `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `MYSQL_PORT` (used if any are set and `DATABASE_URL` is not set)
   - `LEARNZO_SECRET_KEY` / `SECRET_KEY` (required in production)
3. Install and run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tables are created on startup. Ensure `app/static` exists (e.g. `app/static/.gitkeep`).

### API overview

- **Auth**: `POST /auth/register` (email, password, role), `POST /auth/login` → token, role, has_learner.
- **Learners**: `GET /learners/disability-types`, `POST /learners/onboarding` (name, age, disability_type), `GET /learners/me`.
- **VARK**: `GET /vark/questions`, `POST /vark/submit` (20 answers: question_id, yes/no), `GET /vark/result`.
- **Content**: `GET /content/adaptive?topic=...` (returns content adapted to learner VARK + disability).
- **Sessions**: `GET /sessions/history` (current user’s sessions).
- **Teacher**: `GET /teacher/students`, `GET /teacher/students/{learner_id}` (read-only).
- **Dashboard**: `GET /dashboard/learner/{learner_id}`, `/effectiveness/{learner_id}`, `/timeline/{learner_id}` (teacher/parent).

### Disability types (exact values)

`adhd`, `autism`, `dyslexia`, `dyspraxia`, `dyscalculia`, `apd`, `ocd`, `tourette`, `intellectual_disability`, `spd`.

## Frontend

### Setup

```bash
cd frontend
npm install
npm run dev
```

Default dev server: http://localhost:5173. Set `VITE_API_URL` to the backend URL (default `http://127.0.0.1:8000`).
If port 8000 is already in use on your machine, start the backend on another port (e.g. `8001`) and set `VITE_API_URL` accordingly.

### Flow

1. **Register** → email, password, role (student/teacher).
2. **Login** → JWT stored; redirect to `/app`.
3. **Student**: If onboarding not complete → redirect to **Onboarding** (name, age, disability type). Then **VARK** (20 Yes/No questions). Then **Dashboard** with “Learn” and recent activity.
4. **Learning**: Search bar for subject/topic → `GET /content/adaptive?topic=...` → content shown adapted to VARK profile.
5. **Teacher**: Dashboard lists all students; can open a student to see profile, VARK scores, sessions, activity (read-only).

## UI/UX

- Child-friendly: simple language, large buttons, clear navigation.
- Accessibility-first: minimal clutter, readable contrast, clear labels.
- Calm palette (blues/teals), rounded corners, clear hierarchy.

## Production notes

- Set `LEARNZO_SECRET_KEY` and use strong DB credentials.
- Use HTTPS and secure cookies if adding session-based options.
- Run frontend build and serve static files or use a reverse proxy (e.g. Nginx) for API + frontend.

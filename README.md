# AgentUber

## Overview

AgentUber is a two-service web platform:

- **landing** — public landing page with a registration form. Submissions are queued via Celery and written asynchronously to Neo4j.
- **backend** — private dashboard API, protected by JWT authentication (HTTP-only cookie). Admin users have full access; other roles have restricted access.

Both services share a single Neo4j instance and Redis broker. Nginx is **external** to this repository — it proxies to both services from outside the Docker Compose network.

---

## Repository Structure

```
AgentUber/
├── docker-compose.yml          # all services: landing, backend, redis, neo4j
├── .env.example                # environment variable template
├── .gitignore
│
├── landing/                    # public landing + registration worker
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI: GET /, POST /register, GET /demo
│   ├── tasks.py                # Celery task: register_user → Neo4j
│   ├── db.py                   # Neo4j driver + save_user()
│   └── templates/
│       ├── landing.html        # registration form
│       └── demo.html           # post-registration confirmation page
│
└── backend/                    # dashboard API (auth-protected)
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py                 # FastAPI app, exception handlers
    ├── auth.py                 # JWT create/decode, cookie settings
    ├── db.py                   # Neo4j driver + get_user_by_email(), get_all_users()
    ├── dependencies.py         # FastAPI deps: get_current_user, require_admin
    ├── create_admin.py         # interactive script to seed admin user
    ├── routes/
    │   ├── auth.py             # GET /login, POST /login, POST /logout
    │   └── dashboard.py        # GET /dashboard, GET /admin/users
    └── templates/
        ├── login.html          # login form
        └── dashboard.html      # main dashboard UI
```

---

## Services

| Service | Image / Build | Port (internal) | Purpose |
|---|---|---|---|
| `landing` | `./landing` (python:3.12-slim) | `8000` | Public landing page + registration |
| `landing-worker` | `./landing` | — | Celery worker, processes registration queue |
| `backend` | `./backend` (python:3.12-slim) | `8001` | Dashboard API, JWT-protected |
| `redis` | `redis:alpine` | `6379` | Celery broker + result backend |
| `neo4j` | `neo4j:latest` | `7687` | Graph database, stores all User nodes |

All services share a single `internal` Docker network. Only `landing` and `backend` expose ports to the host. Nginx runs outside Docker Compose and proxies to those ports.

---

## Data Model

All users are stored as Neo4j nodes with label `User`:

```
(u:User {
  name:          string,
  email:         string,       # unique identifier
  role:          string,       # "driver" | "passenger" | "operator" | "admin"
  password_hash: string,       # bcrypt — only set for users who can log in
  created_at:    string        # ISO 8601 UTC timestamp
})
```

Users registered via the landing form get `name`, `email`, `role`, `created_at` — **no password**. Admin users are created manually via `create_admin.py` and have a `password_hash`.

---

## Registration Flow

```
POST /register (landing)
  → FastAPI validates form fields (name, email, role)
  → sends task to Redis queue
  → immediately redirects user to /demo
      ↓
  Celery worker picks up the task
  → creates User node in Neo4j
```

---

## Auth Flow (backend / dashboard)

```
GET /dashboard
  → no cookie → redirect to /login

POST /login (email + password form)
  → lookup User in Neo4j by email
  → bcrypt.checkpw(password, user.password_hash)
  → on success: issue JWT, set in HTTP-only cookie, redirect to /dashboard
  → on failure: redirect to /login?error=1

GET /dashboard (cookie present)
  → decode JWT → render dashboard.html with user claims

POST /logout
  → delete cookie → redirect to /login
```

JWT payload: `{ sub: email, role: role, exp: timestamp }`

---

## Roles and Permissions

| Role | Login | Dashboard | GET /admin/users |
|---|---|---|---|
| `driver` | yes (if password_hash set) | yes | no (403) |
| `passenger` | yes (if password_hash set) | yes | no (403) |
| `operator` | yes (if password_hash set) | yes | no (403) |
| `admin` | yes | yes | **yes** |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `NEO4J_URI` | Neo4j bolt URI | `bolt://neo4j:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | — |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `SECRET_KEY` | App secret (landing) | — |
| `UVICORN_PORT` | Landing service port | `8000` |
| `BACKEND_PORT` | Backend service port | `8001` |
| `JWT_SECRET_KEY` | Secret key for signing JWT | — |
| `JWT_EXPIRE_MINUTES` | JWT lifetime in minutes | `60` |
| `SECURE_COOKIES` | Set cookie `Secure` flag | `false` (dev) / `true` (prod) |

In production, set `SECURE_COOKIES=true` — requires HTTPS (handled by external Nginx).

---

## Deployment

### 1. Clone and configure

```bash
git clone <repo-url>
cd AgentUber
cp .env.example .env
# edit .env — set NEO4J_PASSWORD, JWT_SECRET_KEY, SECURE_COOKIES=true
```

### 2. Build and start

```bash
docker compose up -d --build
```

### 3. Create admin user

Run once after first start, when Neo4j is healthy:

```bash
docker compose exec backend python create_admin.py
# prompts for: Name, Email, Password
```

This creates a `User` node with `role: admin` and a bcrypt-hashed password in Neo4j.

### 4. Configure external Nginx

Nginx runs outside Docker Compose. Minimal proxy config:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    # landing
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl;
    server_name app.yourdomain.com;

    # dashboard
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> Ports `8000` and `8001` must be reachable from the host where Nginx runs.

---

## API Reference

### landing (port 8000)

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Landing page (HTML) |
| `POST` | `/register` | Register user. Body: `name`, `email`, `role` (form). Redirects to `/demo`. |
| `GET` | `/demo` | Post-registration confirmation page (HTML) |

### backend (port 8001)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/login` | — | Login form (HTML) |
| `POST` | `/login` | — | Authenticate. Body: `email`, `password` (form). Sets JWT cookie. |
| `POST` | `/logout` | any | Clear JWT cookie. |
| `GET` | `/dashboard` | any role | Dashboard page (HTML) |
| `GET` | `/admin/users` | admin only | List all users (JSON, passwords excluded) |

---

## Development

Run individual services locally without Docker:

```bash
# landing
cd landing
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# celery worker (from landing/)
celery -A tasks worker --loglevel=info
```

Requires `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `REDIS_URL`, `JWT_SECRET_KEY` in environment.

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework (both services) |
| `uvicorn` | ASGI server |
| `celery[redis]` | Async task queue (landing) |
| `neo4j` | Official Neo4j Python driver |
| `python-jose[cryptography]` | JWT encode / decode (backend) |
| `bcrypt` | Password hashing (backend) |
| `jinja2` | HTML templating |
| `python-multipart` | Form data parsing |

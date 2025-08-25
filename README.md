# FastAPI Template with Auth, 2FA, RBAC, Rate Limiting, and Caching

This is a boilerplate FastAPI project featuring authentication, two-factor authentication (2FA), role-based access control (RBAC), per-user rate limiting, and caching. Designed for building secure, high-performance APIs with a production-ready structure.

> ⚡ **Production Ready**: Fully containerized with Docker and Docker Compose, including database migrations, Redis caching, and role-based access control for secure deployments.


## Features

- **User Authentication**: JWT-based login and signup  
- **Two-Factor Authentication (2FA)**: TOTP support  
- **Role-Based Access Control (RBAC)**: Roles like `admin`, `user` 
- **Per-User Rate Limiting**: Using `fastapi-limiter`  
- **Caching**: Redis caching with `fastapi-cache2`  
- **Database Integration**: SQLAlchemy + PostgreSQL  
- **Database Migrations**: Manage schema changes safely with **Alembic**  
- **Login Required Endpoints**: Easily protect routes with `get_current_user` and `require_role` dependencies
- **Production-Ready FastAPI Structure**: Organized with a `utils/` folder for helpers and dependencies  
- **Dependency Injection**: Clean and testable endpoint dependencies  
- **Docker & Docker Compose Integration**: Fully containerized for development and production environments 


## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy / Alembic
- Sqlite, PostgreSQL
- PyJWT for JWT tokens
- PyOTP for 2FA
- fastapi-limiter for per-user rate limiting
- fastapi-cache2 for Redis caching
- Redis (for both rate limiting and caching)
- Docker & Docker Compose (for containerized dev and production setup)


## Project Structure

```text
fastapi-template/
├── app/
│   ├── main.py
│   ├── models/
│   │   ├── user.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── admin.py
│   ├── api/
│   │   ├── auth.py
|   |   ├── admin.py
│   │   ├── user.py
│   ├── utils/
│   │   ├── security.py   # JWT, login/signup helpers
|   |   ├── redis_client.py  # Redis client utils
│   │   ├── rbac.py       # Role-based access checkers
│   │   ├── rate_limit.py # fastapi-limiter per-user limiter
│   │   ├── cache.py      # fastapi-cache2 utils
│   └── database.py
├── tests/
├── alembic/              # Alembic configuration for migrations  
├── requirements.txt
├── Dockerfile
├── docker-compose.yaml
└── README.md

```

## Installation


### 1. Clone the repository

```bash
git clone https://github.com/zwe-htet-paing/fastapi-template.git
cd fastapi-template
```

### 2.Configure Poetry

Create virtualenv inside the project:
```bash
poetry config virtualenvs.in-project true
```

### 3. Install dependencies
```bash
poetry install
```

### 4. Activate environment
```bash
source .venv/bin/activate
```

### 5. Setup environment variable
Create `.env` file in the root directory

```text
DB_DRIVER=postgresql

POSTGRES_HOST=localhost
POSTGRES_USER=test
POSTGRES_PASSWORD=password
POSTGRES_PORT=5432
POSTGRES_DB=test

REDIS_URL=redis://localhost:6379
```


## Database Migrations with Alembic

This project uses **SQLAlchemy** as the ORM and **Alembic** for managing database migrations. Alembic allows you to version your database schema and apply changes safely over time.

#### 1. Initialize Alembic (if not already done)
```code
alembic init alembic
```
This creates an `alembic/` directory and an `alembic.ini` configuration file.


#### 2. Configure Alembic

In `alembic/env.py`, set your database URL to match the project settings:
```code
from app.database import DATABASE_URL_SYNC

config.set_main_option("sqlalchemy.url", DATABASE_URL_SYNC)
```

### 3. Generate a Migration

Whenever you make changes to your SQLAlchemy models:

```bash
alembic revision --autogenerate -m "Initiate tables"
```
- `--autogenerate` compares your models with the database and creates migration scripts.
- `-m`adds a message describing the migration.

### 4. Apply Migrations
```bash
alembic upgrade head
```
- `head` applies all pending migrations.
- To rollback a migration, use `alembic downgrade -1`.


### 5. Optional: Check Migration History
```bash
alembic history
```

### 6. Create Admin User
```bash
python create_admin.py
```

- This will prompt for username and password.
- Example: username `admin`, email `admin@example.com`, password `password123`.
- Creates an admin user in the database ready for login.

### 7. Run FastAPI app
```bash
uvicorn app.main:app --reload
```
- Starts the FastAPI app on http://localhost:8000


## Run with Docker

### 1. Fix/Create `.env` File

Create or update the `.env` file in the root directory with the correct credentials:

```ini
DB_DRIVER=postgresql

POSTGRES_HOST=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
POSTGRES_DB=test

REDIS_URL=redis://redis:6379/0
```

> ⚠️ Important:
> - The `POSTGRES_HOST` must match the Postgres service name in `docker-compose.yaml` (db).
> - Ensure the username/password here match `POSTGRES_USER` and `POSTGRES_PASSWORD`.

### 2. Build Docker Containers
```bash
docker compose up -d --build
```
- Builds the web container and starts db (Postgres) and redis.
- Check logs:

```bash
docker compose logs -f
```

### 3. Apply Database Migrations
```bash
docker compose run --rm web alembic upgrade head
```
- Applies all pending migrations.

### 4. Create Admin User
```bash
docker compose run --rm web python create_admin.py
```
- Creates an admin user in the database.



## Usage

### Role-Based Access Control (RBAC)
```code
from fastapi import Depends
from app.utils.rbac import require_role

@router.get("/users", dependencies=[Depends(require_role("admin"))])
async def admin():
    pass
```

```code
@router.post("/users")
async def update_user_role(current_user: User = Depends(require_role("admin"))):
    pass
```

### Authentication required enpoints
```code
from app.utils.rbac import get_current_user

@router.post("/me")
async def me(current_user: User = Depends(get_current_user)):
    pass
```


### Per-User Rate Limiting
```code
from app.utils.rate_limit import per_user_limiter

@app.get("/protected", dependencies=[Depends(per_user_limiter(times=3, seconds=60))]) # Rate limit to 3 calls per minute
async def protected_endpoint():
    pass
```

### Caching
```code
from fastapi_cache.decorator import cache

@app.get("/cached-data")
@cache(expire=60)  # Cache for 60 seconds
async def get_cached_data():
    # Expensive DB query or computation
    pass
```


---

> ⚠️ **Note:** Some dependencies may not install correctly with Poetry on all systems (e.g., `fastapi-cache2[redis]`, `qrcode`).  
> If you encounter issues, try installing them manually with `pip install <package-name>`.


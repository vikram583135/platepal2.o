# PlatePal Setup Guide

## Prerequisites

Before setting up PlatePal, ensure you have the following installed:

- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher
- Git

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Create a PostgreSQL database:

```sql
CREATE DATABASE platepal;
CREATE USER platepal_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE platepal TO platepal_user;
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and update with your settings:

```bash
cp .env.example .env
```

Update the following in `.env`:
- `SECRET_KEY`: Generate a secure key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Your PostgreSQL credentials
- `REDIS_HOST`, `REDIS_PORT`: Your Redis connection details

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Seed Sample Data

```bash
python manage.py seed_data
```

This creates test accounts:
- Admin: admin@platepal.com / admin123
- Customer: customer@platepal.com / customer123
- Restaurant: restaurant@platepal.com / restaurant123
- Rider: rider@platepal.com / rider123

### 8. Start Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

### 3. Start Development Server

For Customer app:
```bash
npm run dev:customer
```

For Restaurant app:
```bash
npm run dev:restaurant
```

For Delivery app:
```bash
npm run dev:delivery
```

For Admin app:
```bash
npm run dev:admin
```

## Running Redis

Redis is required for WebSocket channels and caching.

**For detailed Redis installation and configuration instructions, see [Redis Setup Guide](REDIS_SETUP.md).**

Quick start:

```bash
# macOS (using Homebrew)
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:latest

# Windows (WSL)
# See REDIS_SETUP.md for Windows-specific instructions
```

## Running PostgreSQL

```bash
# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Linux
sudo apt-get install postgresql
sudo systemctl start postgresql

# Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:latest
```

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running
- Verify database credentials in `.env`
- Check if database exists: `psql -l`

### Redis Connection Issues

- Ensure Redis is running: `redis-cli ping` (should return PONG)
- Check Redis port in `.env`

### Frontend Build Issues

- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

### WebSocket Connection Issues

- Ensure Redis is running
- Check CORS settings in backend
- Verify WebSocket URL in frontend `.env`

## Next Steps

1. Explore the API documentation at `http://localhost:8000/api/docs/`
2. Test the customer interface at `http://localhost:3000`
3. Test the restaurant interface at `http://localhost:3001`
4. Review the code structure and customize as needed


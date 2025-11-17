# PlatePal - Food Ordering Platform

A full-stack food ordering platform similar to Zomato, built with Django REST Framework and React.

## Features

- **Customer Interface**: Browse restaurants, place orders, track deliveries
- **Restaurant Interface**: Manage menu, accept orders, track sales
- **Delivery Interface**: Accept deliveries, track location, manage earnings
- **Admin Interface**: User management, analytics, marketplace controls
- **Real-time Updates**: WebSocket integration for live order tracking
- **Payment Processing**: Mock payment system (ready for gateway integration)

## Tech Stack

### Backend
- Django 4.2+
- Django REST Framework
- Django Channels (WebSocket)
- PostgreSQL
- Redis
- JWT Authentication

### Frontend
- React 18+
- TypeScript
- Vite
- TailwindCSS
- React Query
- Zustand
- Leaflet (Maps)

## Project Structure

```
platepal/
├── backend/          # Django backend
│   ├── apps/        # Django apps
│   ├── channels/    # WebSocket consumers
│   └── platepal/    # Project settings
├── frontend/         # React frontend
│   ├── apps/        # Customer, Restaurant, Delivery, Admin apps
│   └── packages/    # Shared packages (UI, API, utils)
├── shared/          # Shared schemas
├── docs/            # Documentation
└── tests/           # Integration tests
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis (see [Redis Setup Guide](docs/REDIS_SETUP.md) for detailed installation instructions)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
```

3. Activate virtual environment:
```bash
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
venv\Scripts\activate.bat

# On macOS/Linux:
source venv/bin/activate
```

4. Install dependencies:
```bash
# Make sure virtual environment is activated first
pip install -r requirements.txt

# Or on Windows, if pip doesn't work:
python -m pip install -r requirements.txt
```

5. Create `.env` file from `.env.example`:
```bash
# On Windows (PowerShell):
Copy-Item .env.example .env

# On Windows (Command Prompt):
copy .env.example .env

# On macOS/Linux:
cp .env.example .env
```

6. Update `.env` with your database and Redis credentials

7. Run migrations:
```bash
python manage.py migrate
```

8. Create superuser:
```bash
python manage.py createsuperuser
```

9. Seed sample data:
```bash
python manage.py seed_data
```

10. Run development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

4. Run customer app:
```bash
npm run dev:customer
```

5. Run other apps:
```bash
npm run dev:restaurant
npm run dev:delivery
npm run dev:admin
```

## Test Accounts

After running `seed_data`, you can use these accounts:

### Admin & Customer Accounts
- **Admin**: admin@platepal.com / admin123
- **Customer**: customer@platepal.com / customer123
- **Rider**: rider@platepal.com / rider123

### Restaurant Accounts
- **Pizza Palace Mumbai** (Italian): restaurant@platepal.com / restaurant123
- **Mumbai Masala House** (Indian): mumbai@platepal.com / masala123
- **Sakura Sushi Bar** (Japanese): sakura@platepal.com / sakura123
- **Bangkok Express** (Thai): thai@platepal.com / thai123
- **Koramangala Smokehouse** (BBQ): koramangala@platepal.com / bangalore123
- **Indiranagar Green Bowl** (Plant-based): indiranagar@platepal.com / indira123
- **MG Road Spice Studio** (Modern Indian): bangalore@platepal.com / bangalore123
- **Whitefield Vegan CoLab** (Vegan): whitefield@platepal.com / white123

See `docs/RESTAURANT_CREDENTIALS.md` for the full seeded matrix.

All restaurants have active menus with multiple dishes, proper INR pricing, and food images.

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Development

### Backend

- Run tests: `pytest`
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`

### Frontend

- Type check: `npm run type-check`
- Lint: `npm run lint`
- Build: `npm run build:customer` (or restaurant/delivery/admin)

## Environment Variables

### Backend (.env)
- `SECRET_KEY`: Django secret key
- `DEBUG`: True/False
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: PostgreSQL credentials
- `REDIS_HOST`, `REDIS_PORT`: Redis connection

### Frontend (.env)
- `VITE_API_BASE_URL`: Backend API URL
- `VITE_WS_URL`: WebSocket URL

## License

MIT


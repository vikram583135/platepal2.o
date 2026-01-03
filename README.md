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
python manage.py seed_admin_data
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

## Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/platepal.git
   cd platepal
   ```
3. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Making Changes

1. Follow the [Setup Instructions](#setup-instructions) to get the project running
2. Make your changes following our coding standards:
   - **Backend**: Follow PEP 8 style guide for Python
   - **Frontend**: Use TypeScript, follow ESLint rules
3. Write or update tests as needed
4. Ensure all tests pass before submitting

### Submitting Changes

1. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "feat: add new feature description"
   ```
   We follow [Conventional Commits](https://www.conventionalcommits.org/) format.

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request** against the `main` branch

### Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues using `#issue-number`
- Ensure CI checks pass
- Be responsive to feedback and review comments

### Types of Contributions

We appreciate all kinds of contributions:

- 🐛 **Bug Reports**: Found a bug? [Open an issue](../../issues/new)
- ✨ **Feature Requests**: Have an idea? [Start a discussion](../../discussions)
- 📖 **Documentation**: Help improve our docs
- 🧪 **Testing**: Add or improve tests
- 💻 **Code**: Fix bugs or implement features

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for everyone. We pledge to make participation in our project a harassment-free experience regardless of age, body size, disability, ethnicity, gender identity, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or discriminatory comments
- Personal or political attacks
- Publishing others' private information without consent
- Any conduct inappropriate in a professional setting

### Enforcement

Violations may be reported to the project maintainers. All reports will be reviewed and addressed appropriately.

---

## Getting Help

Need help? Here's how to get support:

- 📚 **Documentation**: Check our [docs](./docs) folder for guides
- 💬 **Discussions**: Ask questions in [GitHub Discussions](../../discussions)
- 🐛 **Bug Reports**: [Open an issue](../../issues/new) for bugs
- 📧 **Email**: Contact maintainers for private concerns

---

## Acknowledgements

- Built with [Django](https://djangoproject.com/) and [React](https://react.dev/)
- UI styled with [TailwindCSS](https://tailwindcss.com/)
- Maps powered by [Leaflet](https://leafletjs.com/)
- Icons from [Heroicons](https://heroicons.com/)

Special thanks to all contributors who help make PlatePal better!

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

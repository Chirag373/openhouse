# Real Estate Platform API

Django REST Framework application for managing real estate listings with multiple user roles (Realtors, Lenders, Brokers, Partners, and Promoters).

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment tool (venv or virtualenv)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Create and activate virtual environment

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Navigate to the core directory

```bash
cd core
```

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Project Structure

```
core/
├── api/                    # Main API application
│   ├── models.py          # Database models
│   ├── serializers.py     # API serializers
│   ├── views.py           # API views
│   └── urls.py            # API URL routing
├── core/                   # Project settings
│   ├── settings.py        # Django settings
│   └── urls.py            # Main URL configuration
├── templates/             # HTML templates
├── media/                 # User uploaded files (created automatically)
├── manage.py              # Django management script
└── db.sqlite3            # SQLite database
```

## API Endpoints

### Authentication
- `POST /api/signup/` - User registration
- `POST /api/login/` - User login

### User Profiles
- `GET /api/realtor-profile/me/` - Get realtor profile
- `PUT /api/realtor-profile/update_profile/` - Update realtor profile
- `POST /api/realtor-profile/upload_photo/` - Upload profile photo

Similar endpoints exist for:
- `/api/lender-profile/`
- `/api/broker-profile/`
- `/api/partner-profile/`
- `/api/promoter-profile/`

### Properties
- `GET /api/properties/` - List user's properties
- `POST /api/properties/` - Create new property
- `GET /api/properties/public_listings/` - Get all active listings
- `POST /api/properties/{id}/upload_photos/` - Upload property photos

### Open Houses & Perks
- `GET /api/open-houses/` - List open houses
- `POST /api/open-houses/` - Create open house
- `GET /api/perks/` - List perks
- `POST /api/perks/` - Create perk

## User Roles

The platform supports five user roles:
- **Realtor**: Manage property listings
- **Lender**: Provide financing information
- **Broker**: Manage brokerage services
- **Partner**: Offer related services (title, inspection, etc.)
- **Promoter**: Marketing and promotional services

## Development

### Running tests

```bash
pytest
```

### Code formatting

```bash
black .
isort .
```

### Linting

```bash
flake8
```

## Production Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Configure a production database (PostgreSQL recommended)
3. Set up proper `SECRET_KEY` and `ALLOWED_HOSTS`
4. Use gunicorn or daphne as WSGI/ASGI server
5. Configure static files serving
6. Set up media files storage (AWS S3, etc.)

## Environment Variables

Create a `.env` file in the core directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## License

[Your License Here]

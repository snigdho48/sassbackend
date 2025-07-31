# SaaS Platform - Separated Frontend/Backend

This project consists of a Django REST API backend and a React frontend that run independently.

## Architecture

- **Backend**: Django REST API (Port 8000)
- **Frontend**: React Application (Port 3000)
- **Database**: MySQL/SQLite
- **Authentication**: JWT Tokens

## Backend Setup (Django API)

### Prerequisites
- Python 3.8+
- MySQL (optional, falls back to SQLite)

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start the API server
python manage.py runserver 8000
```

### API Endpoints
- **API Root**: `http://localhost:8000/api/`
- **Admin**: `http://localhost:8000/admin/`
- **Swagger Docs**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`

### Available APIs
- Authentication: `/api/auth/`
- Water Analysis: `/api/water-analysis/`
- Water Recommendations: `/api/water-recommendations/`
- Water Trends: `/api/water-trends/`
- Users: `/api/users/`

## Frontend Setup (React)

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation
```bash
cd frontend

# Install dependencies
npm install
# or
yarn install

# Start development server
npm start
# or
yarn start
```

### Frontend URL
- **Development**: `http://localhost:3000`

## Development Workflow

1. **Start Backend**: Run Django server on port 8000
2. **Start Frontend**: Run React dev server on port 3000
3. **Access Frontend**: Open `http://localhost:3000` in browser
4. **API Access**: Frontend will make API calls to `http://localhost:8000/api/`

## CORS Configuration

The backend is configured to allow requests from:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://192.168.68.65:3000`

## Authentication

The system uses JWT tokens for authentication:
- Access tokens expire in 1 hour
- Refresh tokens expire in 7 days
- Frontend should store tokens and include them in API requests

## Environment Variables

Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=sass_db
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
```

## Production Deployment

### Backend
- Use a production WSGI server (Gunicorn, uWSGI)
- Configure a reverse proxy (Nginx)
- Set `DEBUG=False`
- Use environment variables for sensitive data

### Frontend
- Build the React app: `npm run build`
- Serve static files through a web server
- Configure API base URL for production

## API Documentation

- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **Browsable API**: Available at all API endpoints when accessed through a browser 
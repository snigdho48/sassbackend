# SaaS Platform - Technical Data Analytics

A comprehensive SaaS platform for technical data logging and analytics, built with Django backend and React frontend.

## 🚀 Features

### Core Functionality
- **User Authentication** - Role-based access control with secure login
- **Data Entry Interface** - Log technical data with calculation logic
- **Analytics Dashboard** - Interactive charts and performance metrics
- **PDF Report Generation** - Automated report creation and export
- **Real-time Analytics** - Live data visualization and insights

### Technical Stack
- **Backend**: Django 5.2 + MySQL
- **Frontend**: React 18 + Tailwind CSS
- **Database**: MySQL with SQLite fallback
- **Authentication**: JWT tokens
- **Charts**: Recharts library
- **Deployment**: Shared hosting ready

## 📋 Requirements

### Backend Requirements
- Python 3.8+
- MySQL 5.7+ (or SQLite for development)
- Virtual environment

### Frontend Requirements
- Node.js 16+
- npm or yarn

## 🛠️ Installation

### 1. Backend Setup

```bash
# Navigate to project directory
cd /path/to/sass

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database settings

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### 3. Database Configuration

#### MySQL Setup
```sql
CREATE DATABASE sass_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sass_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON sass_db.* TO 'sass_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Environment Variables (.env)
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_NAME=sass_db
DB_USER=sass_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

## 🏗️ Project Structure

```
sass/
├── backend/
│   ├── sass_project/     # Django settings
│   ├── users/           # User management
│   ├── data_entry/      # Data models & logic
│   ├── dashboard/       # Dashboard functionality
│   ├── reports/         # PDF generation
│   └── api/            # API endpoints
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   └── contexts/    # React contexts
│   └── public/          # Static files
└── requirements.txt
```

## 🔧 Configuration

### Django Settings
- Custom user model with role-based access
- MySQL database configuration
- Static files and media handling
- Authentication settings
- CORS configuration for frontend

### React Configuration
- Tailwind CSS with custom theme
- React Router for navigation
- React Query for data fetching
- Axios for API communication

## 🚀 Usage

### User Roles
- **Admin**: Full system access
- **Manager**: Data management and reports
- **Operator**: Data entry and viewing
- **Viewer**: Read-only access

### Data Entry
1. Select data category
2. Enter technical values
3. Add notes and metadata
4. Save for analytics processing

### Analytics
- Real-time dashboard with charts
- Performance metrics
- Trend analysis
- Custom date ranges

### Reports
- Generate PDF reports
- Custom date ranges
- Multiple report types
- Automated scheduling

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `GET /api/auth/user/` - Current user info

### Data Management
- `GET /api/data/categories/` - List categories
- `POST /api/data/entries/` - Create data entry
- `GET /api/data/analytics/` - Analytics data

### Reports
- `POST /api/reports/generate/` - Generate report
- `GET /api/reports/` - List reports
- `GET /api/reports/{id}/download/` - Download PDF

## 🎨 UI Components

### Dashboard
- Interactive charts (Line, Bar, Pie)
- Real-time metrics
- Activity feed
- Performance indicators

### Data Entry
- Category selection
- Form validation
- Data table with CRUD
- Bulk operations

### Reports
- Report type selection
- Date range picker
- PDF preview
- Download functionality

## 🔒 Security Features

- JWT authentication
- Role-based access control
- Input validation
- CSRF protection
- Secure password handling
- HTTPS ready

## 📱 Responsive Design

- Mobile-first approach
- Tablet and desktop optimized
- Touch-friendly interface
- Progressive web app features

## 🚀 Deployment

### Backend Deployment
1. Configure production settings
2. Set up MySQL database
3. Configure static files
4. Set up web server (nginx/Apache)
5. Configure SSL certificate

### Frontend Deployment
1. Build production version
2. Upload to web server
3. Configure API endpoints
4. Set up CDN for assets

### Shared Hosting
- Compatible with cPanel/DirectAdmin
- MySQL database support
- Static file serving
- .htaccess configuration

## 🧪 Testing

### Backend Tests
```bash
python manage.py test
```

### Frontend Tests
```bash
npm test
```

## 📈 Performance

- Optimized database queries
- Caching strategies
- Lazy loading components
- Image optimization
- Code splitting

## 🔧 Development

### Adding New Features
1. Create Django models
2. Add API endpoints
3. Create React components
4. Update routing
5. Test functionality

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## 📝 Documentation

- API documentation
- Component library
- User guides
- Deployment guides

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check documentation
- Review troubleshooting guide

## 🔄 Updates

### Version History
- v1.0.0 - Initial release
- v1.1.0 - Added analytics features
- v1.2.0 - Enhanced reporting

### Upcoming Features
- AI-powered insights
- Advanced analytics
- Mobile app
- API integrations

---

**Built with ❤️ for industrial data analytics** 
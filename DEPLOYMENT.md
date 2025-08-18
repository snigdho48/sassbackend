# Linux Server Deployment Guide

This guide will help you deploy your Django API backend on a Linux server using Gunicorn and Nginx.

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- Root or sudo access
- Domain name (optional, but recommended for SSL)
- SSH access to your server

## Quick Deployment (Root User)

### 1. Upload Your Code

First, upload your project files to the server. You can use:
- Git clone
- SCP/SFTP
- rsync

```bash
# Option 1: Git clone
git clone https://github.com/your-username/your-repo.git /projects/sassbackend

# Option 2: Upload via SCP
scp -r ./sass root@your-server:/projects/sassbackend
```

### 2. Run the Quick Setup Script

```bash
# Make the script executable
chmod +x setup-root.sh

# Run the quick setup script (as root)
./setup-root.sh
```

### 3. Alternative: Full Deployment Script

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment script (as root)
./deploy.sh
```

The script will:
- Install all required packages
- Set up the database
- Configure Gunicorn and Nginx
- Set up SSL (optional)
- Start all services

## Manual Deployment

If you prefer to deploy manually, follow these steps:

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx mysql-server mysql-client git curl
```

### 2. Project Setup

```bash
# Create project directory
mkdir -p /projects/sassbackend

# Copy your project files to /projects/sassbackend/
cd /projects/sassbackend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Secure MySQL installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -e "CREATE DATABASE sass_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER 'sass_user'@'localhost' IDENTIFIED BY 'your_secure_password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON sass_db.* TO 'sass_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

### 4. Environment Configuration

Create a `.env` file in `/projects/sassbackend/`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
DB_NAME=sass_db
DB_USER=sass_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=3306
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 5. Django Setup

```bash
# Set environment variable
export DJANGO_SETTINGS_MODULE=sass_project.settings_production

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### 6. Gunicorn Setup

```bash
# Create log directories
mkdir -p /var/log/gunicorn /var/run/gunicorn

# Copy service file
cp sass-api.service /etc/systemd/system/

# Enable and start service
systemctl daemon-reload
systemctl enable sass-api
systemctl start sass-api
```

### 7. Nginx Setup

```bash
# Copy Nginx configuration
cp nginx-sass-api.conf /etc/nginx/sites-available/sassbackend

# Enable site
ln -sf /etc/nginx/sites-available/sassbackend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

### 8. SSL Setup (Optional)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Configuration Files

### Update Domain Names

Before deployment, update these files with your actual domain:

1. **sass_project/settings_production.py**:
   ```python
   ALLOWED_HOSTS = [
       'your-actual-domain.com',
       'www.your-actual-domain.com',
       'your-server-ip',
   ]
   ```

2. **nginx-sass-api.conf**:
   ```nginx
   server_name your-actual-domain.com www.your-actual-domain.com;
   ```

3. **deploy.sh**:
   ```bash
   DOMAIN="your-actual-domain.com"
   ```

### Security Considerations

1. **Firewall Setup**:
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 'Nginx Full'
   sudo ufw --force enable
   ```

2. **Database Security**:
   - Use strong passwords
   - Limit database access to localhost
   - Regular backups

3. **File Permissions**:
   ```bash
   sudo chown -R www-data:www-data /var/www/sass
   sudo chmod -R 755 /var/www/sass
   ```

## Monitoring and Maintenance

### Service Management

```bash
# Check service status
sudo systemctl status sass-api
sudo systemctl status nginx

# Restart services
sudo systemctl restart sass-api
sudo systemctl restart nginx

# View logs
sudo journalctl -u sass-api -f
sudo tail -f /var/log/nginx/error.log
```

### Updates

```bash
# Update code
cd /var/www/sass
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart service
sudo systemctl restart sass-api
```

### Backups

```bash
# Database backup
mysqldump -u sass_user -p sass_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Files backup
tar -czf sass_backup_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/sass/
```

## Troubleshooting

### Common Issues

1. **Permission Denied**:
   ```bash
   sudo chown -R www-data:www-data /var/www/sass
   sudo chmod -R 755 /var/www/sass
   ```

2. **Database Connection Error**:
   - Check MySQL service: `sudo systemctl status mysql`
   - Verify credentials in `.env`
   - Check database exists: `sudo mysql -e "SHOW DATABASES;"`

3. **Static Files Not Loading**:
   ```bash
   python manage.py collectstatic --noinput
   sudo systemctl restart sass-api
   ```

4. **Nginx 502 Bad Gateway**:
   - Check Gunicorn is running: `sudo systemctl status sass-api`
   - Check logs: `sudo journalctl -u sass-api -f`

### Log Locations

- **Gunicorn logs**: `/var/log/gunicorn/`
- **Nginx logs**: `/var/log/nginx/`
- **System logs**: `sudo journalctl -u sass-api`

## Performance Optimization

1. **Database Optimization**:
   - Add database indexes
   - Optimize queries
   - Use connection pooling

2. **Caching**:
   - Redis for session storage
   - Django cache framework
   - CDN for static files

3. **Monitoring**:
   - Set up monitoring tools (Prometheus, Grafana)
   - Log aggregation (ELK stack)
   - Uptime monitoring

## Security Checklist

- [ ] HTTPS enabled
- [ ] Strong database passwords
- [ ] Firewall configured
- [ ] Regular security updates
- [ ] Backup strategy in place
- [ ] Monitoring and alerting
- [ ] Access logs reviewed
- [ ] SSL certificate auto-renewal 
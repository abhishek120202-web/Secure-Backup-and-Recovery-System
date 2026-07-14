# Installation Guide

## Secure VMware Backup and Recovery System

Complete installation and setup instructions for the Flask application.

---

## 📋 Prerequisites

Before you begin, ensure you have:

- **Windows 10/11** or **Linux/macOS**
- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **MySQL 8.0+** ([Download](https://dev.mysql.com/downloads/mysql/))
- **Git** ([Download](https://git-scm.com/))
- **pip** (included with Python)

---

## 🚀 Quick Start (Windows)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/secure-backup-recovery-system.git
cd secure-backup-recovery-system
```

### 2. Run Setup Script
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
.\setup.ps1
```

### 3. Configure Environment
```bash
# Edit .env with your database credentials
notepad .env
```

Example `.env`:
```
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
SECRET_KEY=your-secret-key-here
DEV_DATABASE_URL=mysql+pymysql://root:password@localhost:3306/secure_backup_dev
```

### 4. Initialize Database
```bash
# Create MySQL databases
mysql -u root -p < database_setup.sql

# Or manually:
mysql -u root -p
CREATE DATABASE secure_backup_dev;
CREATE DATABASE secure_backup_prod;
EXIT;
```

### 5. Run Application
```bash
python run.py
```

Visit: `http://localhost:5000`

---

## 🐧 Detailed Setup (Linux/macOS)

### 1. System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv python3-pip mysql-server

# macOS
brew install python@3.12 mysql
```

### 2. Clone Repository
```bash
git clone https://github.com/yourusername/secure-backup-recovery-system.git
cd secure-backup-recovery-system
```

### 3. Create Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your configuration
```

### 6. Setup MySQL Database
```bash
# Start MySQL
sudo systemctl start mysql

# Create databases
mysql -u root -p
CREATE DATABASE secure_backup_dev;
CREATE DATABASE secure_backup_prod;
EXIT;
```

### 7. Run Application
```bash
python run.py
```

---

## 🗄️ Database Configuration

### MySQL Connection String
```
mysql+pymysql://username:password@hostname:3306/database_name
```

### Example Configurations

**Development (Local MySQL)**
```
DEV_DATABASE_URL=mysql+pymysql://root:password@localhost:3306/secure_backup_dev
```

**Development (SQLite)**
```
DEV_DATABASE_URL=sqlite:///instance/dev.db
```

**Production (Remote MySQL)**
```
DATABASE_URL=mysql+pymysql://app_user:secure_password@db.example.com:3306/secure_backup_prod
```

### Create Admin User
```bash
flask shell
>>> from app.models.user import User
>>> from app.models.user import db
>>> admin = User(username='admin', email='admin@example.com', role='admin', full_name='Administrator')
>>> admin.set_password('admin123')
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

---

## 🔒 Security Configuration

### Production Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Configure strong database password
- [ ] Enable HTTPS/SSL
- [ ] Set secure session cookies
- [ ] Configure rate limiting
- [ ] Setup email for notifications
- [ ] Review and update user permissions
- [ ] Enable audit logging
- [ ] Configure backup retention policies
- [ ] Test backup and recovery procedures

### Environment Variables
```bash
# Required for Production
SECRET_KEY=your-very-secure-random-key-here
DATABASE_URL=mysql+pymysql://user:password@host/db
FLASK_ENV=production
FLASK_DEBUG=False

# Optional but Recommended
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
LOG_TO_STDOUT=True
LOG_LEVEL=INFO
```

---

## 📦 Dependency Management

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### View Installed Packages
```bash
pip list
pip show flask
```

### Add New Dependency
```bash
pip install package-name
pip freeze > requirements.txt
```

---

## 🧪 Testing

### Run Tests
```bash
pytest
pytest --cov=app
pytest -v
```

### Code Quality
```bash
# Format code
black app/

# Check style
flake8 app/

# Sort imports
isort app/

# Lint
pylint app/
```

---

## 🚢 Deployment

### Using Gunicorn (Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Using Docker
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_ENV=production

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name backup.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔧 Troubleshooting

### Python Not Found
```bash
# Windows: Add Python to PATH
setx PATH "%PATH%;C:\Users\Username\AppData\Local\Programs\Python\Python312"

# Linux/macOS
which python3
python3 --version
```

### MySQL Connection Error
```bash
# Test connection
mysql -u root -p -h localhost

# Check MySQL is running
systemctl status mysql  # Linux
brew services list     # macOS
```

### Port Already in Use
```bash
# Change port in .env
FLASK_PORT=8000

# Or kill process using port 5000
lsof -ti:5000 | xargs kill -9  # Linux/macOS
netstat -ano | findstr :5000   # Windows
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Database Migration Issues
```bash
# Reset migrations (development only!)
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

---

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Flask-Login](https://flask-login.readthedocs.io/)
- [MySQL Connector](https://dev.mysql.com/doc/connector-python/en/)
- [Python Cryptography](https://cryptography.io/)

---

## 📞 Support

For issues or questions:
1. Check this installation guide
2. Review application logs in `logs/` directory
3. Consult Flask documentation
4. Contact development team

---

**Last Updated:** December 2024  
**Version:** 1.0.0

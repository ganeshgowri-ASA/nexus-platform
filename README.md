# 🚀 NEXUS Platform

**NEXUS**: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## 🎯 Overview

NEXUS Platform is a comprehensive productivity suite that combines enterprise-grade authentication, AI capabilities, and integrated tools for modern teams and individuals.

---

## 📋 Current Implementation Status

### ✅ Phase 1 - Session 3: Authentication & Authorization System (COMPLETE)

A production-ready authentication and authorization system with:

#### 🔐 Authentication Features
- Email/Password registration with comprehensive validation
- Secure password hashing using bcrypt (12 rounds)
- JWT token-based authentication (access + refresh tokens)
- Login with "Remember me" functionality
- Session persistence with Streamlit integration
- Password reset workflow with secure tokens
- Email verification system
- Account lockout after 5 failed login attempts
- Configurable session timeout (default: 60 minutes)

#### 🎭 Authorization (RBAC) Features
- Role-Based Access Control with 4 default roles:
  - **Admin**: Full system access
  - **Manager**: Elevated privileges
  - **User**: Standard access
  - **Guest**: Limited access
- Granular permission system per module
- Permission decorators: `@require_auth`, `@require_role`, `@require_admin`
- Role hierarchy and management
- Dynamic UI based on user roles

#### 🌐 OAuth Integration
- Google OAuth 2.0 support
- Microsoft OAuth 2.0 support
- Social login buttons with auto-linking
- Automatic avatar retrieval from OAuth providers

#### 🔒 Security Features
- CSRF protection
- Rate limiting (5 login attempts per minute)
- Password strength validation with real-time feedback
- Secure session cookies (HTTP-only, Secure, SameSite)
- SQL injection protection via SQLAlchemy ORM
- XSS protection through input sanitization

#### 🎨 User Interface
- Beautiful gradient design with modern UI
- Real-time password strength indicator
- Form validation with instant feedback
- Success/error toast notifications
- Auto-redirect after authentication
- Profile picture upload support
- Responsive, mobile-friendly design

---

## 🏗️ Project Structure

```
nexus-platform/
├── app.py                          # Main Streamlit application
├── init_db.py                      # Database initialization script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── AUTH_DOCUMENTATION.md           # Detailed auth system documentation
├── modules/
│   ├── auth/                       # Authentication & Authorization
│   │   ├── authentication.py       # Login, register, logout
│   │   ├── authorization.py        # RBAC system
│   │   ├── session_manager.py      # Streamlit session management
│   │   ├── password_utils.py       # Password utilities
│   │   ├── oauth.py                # OAuth integration
│   │   └── middleware.py           # Auth decorators
│   └── database/                   # Database layer
│       ├── models.py               # SQLAlchemy models
│       └── connection.py           # Database connection
├── pages/                          # Streamlit pages
│   ├── 1_🔐_Login.py               # Login page
│   ├── 2_📝_Register.py            # Registration page
│   ├── 3_👤_Profile.py             # User profile
│   └── 4_🔑_Reset_Password.py      # Password reset
└── .streamlit/
    └── config.toml                 # Streamlit configuration
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nexus-platform
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Access the application**
   - Open your browser to: http://localhost:8501
   - Register a new account
   - Start using NEXUS Platform!

---

## 📚 Documentation

- **[Authentication Documentation](AUTH_DOCUMENTATION.md)** - Complete guide to the authentication system
- **API Reference** - Available in AUTH_DOCUMENTATION.md
- **Security Best Practices** - See AUTH_DOCUMENTATION.md

---

## 🔧 Configuration

### Database Options

**SQLite (Development - Default)**
```bash
DATABASE_URL=sqlite:///./nexus_platform.db
```

**PostgreSQL (Production)**
```bash
DATABASE_URL=postgresql://user:password@localhost/nexus_platform
```

**MySQL (Production)**
```bash
DATABASE_URL=mysql://user:password@localhost/nexus_platform
```

### OAuth Setup (Optional)

**Google OAuth**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add to `.env`:
   ```bash
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

**Microsoft OAuth**
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register a new application
3. Add redirect URI
4. Create client secret
5. Add to `.env`:
   ```bash
   MICROSOFT_CLIENT_ID=your-client-id
   MICROSOFT_CLIENT_SECRET=your-client-secret
   ```

---

## 🛡️ Security

### Password Requirements
- Minimum 8 characters (recommended 12+)
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character
- Not a common/weak password

### Production Deployment Checklist
- [ ] Use PostgreSQL or MySQL (not SQLite)
- [ ] Set strong SECRET_KEY in environment
- [ ] Enable HTTPS
- [ ] Configure secure cookie flags
- [ ] Set up email service for verification
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor login attempts
- [ ] Implement audit logging

---

## 🎯 Roadmap

### ✅ Completed
- Phase 1 - Session 3: Authentication & Authorization System

### 🚧 Upcoming Phases
- Phase 1 - Session 4: Core Dashboard & Navigation
- Phase 2: Document Processing (Word, Excel, PPT)
- Phase 3: Communication Tools (Email, Chat, Meetings)
- Phase 4: Project Management
- Phase 5: Analytics & Reporting
- Phase 6: AI Integration & Advanced Features

---

## 👥 User Roles

| Role | Description | Default Permissions |
|------|-------------|-------------------|
| **Admin** | Full system access | All permissions |
| **Manager** | Elevated privileges | Most operations except role management |
| **User** | Standard access | Read/write own data |
| **Guest** | Limited access | Read-only access to public content |

---

## 📖 Usage Examples

### Protecting a Page (Require Login)
```python
from modules.auth import StreamlitSessionManager

# Require authentication
StreamlitSessionManager.require_auth()

# Your page content here
st.write("This is a protected page")
```

### Require Admin Access
```python
from modules.auth import StreamlitSessionManager

# Only admins can access
StreamlitSessionManager.require_role("admin")

st.write("Admin-only content")
```

### Get Current User Information
```python
from modules.auth import StreamlitSessionManager

user = StreamlitSessionManager.get_current_user()
if user:
    st.write(f"Welcome, {user['full_name']}!")
    st.write(f"Your roles: {', '.join(user['roles'])}")
```

### Using Decorators
```python
from modules.auth.middleware import require_auth, require_admin

@require_auth()
def protected_function():
    st.write("Authenticated users only")

@require_admin()
def admin_function():
    st.write("Admins only")
```

---

## 🧪 Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Type Checking
```bash
mypy modules/
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

© 2024 NEXUS Platform. All rights reserved.

---

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Email: support@nexusplatform.com

---

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [bcrypt](https://github.com/pyca/bcrypt/) - Password hashing
- [python-jose](https://github.com/mpdavis/python-jose) - JWT tokens
- [Claude AI](https://www.anthropic.com/) - AI integration

---

**NEXUS Platform** - Empowering productivity through unified tools and AI 🚀

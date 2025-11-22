# NEXUS Platform - Authentication & Authorization System

## 📚 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Architecture](#architecture)
6. [Usage Guide](#usage-guide)
7. [API Reference](#api-reference)
8. [Security](#security)
9. [Configuration](#configuration)
10. [Development](#development)

---

## 🎯 Overview

NEXUS Platform provides a production-ready authentication and authorization system built with Streamlit, SQLAlchemy, and modern security practices. The system implements Role-Based Access Control (RBAC), JWT authentication, OAuth integration, and comprehensive security features.

## ✨ Features

### Authentication
- ✅ **Email/Password Registration** - Secure user registration with validation
- ✅ **Secure Password Hashing** - Bcrypt with 12 rounds
- ✅ **Login System** - Email/username login with "Remember me"
- ✅ **JWT Tokens** - Access tokens (1 hour) + Refresh tokens (30 days)
- ✅ **Session Management** - Persistent Streamlit sessions with timeout
- ✅ **Password Reset** - Secure token-based password recovery
- ✅ **Email Verification** - Account verification workflow
- ✅ **Account Lockout** - Protection after 5 failed login attempts
- ✅ **Session Timeout** - Configurable timeout (default: 60 minutes)

### Authorization (RBAC)
- ✅ **Role System** - Admin, Manager, User, Guest roles
- ✅ **Permissions** - Granular permission system per module
- ✅ **Decorators** - `@require_auth`, `@require_role`, `@require_admin`
- ✅ **Role Hierarchy** - Hierarchical role management
- ✅ **Dynamic UI** - Role-based UI visibility control

### OAuth Integration
- ✅ **Google OAuth 2.0** - Sign in with Google
- ✅ **Microsoft OAuth 2.0** - Sign in with Microsoft
- ✅ **Auto-linking** - Link OAuth to existing accounts
- ✅ **Avatar Support** - Automatic avatar from OAuth providers

### Security
- ✅ **CSRF Protection** - Cross-site request forgery protection
- ✅ **Rate Limiting** - 5 login attempts per minute
- ✅ **Password Validation** - Complexity requirements enforced
- ✅ **Secure Sessions** - HTTP-only, Secure, SameSite cookies
- ✅ **SQL Injection Protection** - SQLAlchemy ORM
- ✅ **XSS Protection** - Input sanitization

### UI/UX
- ✅ **Beautiful Design** - Gradient backgrounds and modern UI
- ✅ **Real-time Validation** - Password strength indicator
- ✅ **Toast Messages** - Success/error notifications
- ✅ **Auto-redirect** - Seamless navigation after login
- ✅ **Responsive** - Mobile-friendly design
- ✅ **Form Validation** - Client-side and server-side

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd nexus-platform
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Step 5: Initialize Database
```bash
python init_db.py
```

### Step 6: Run Application
```bash
streamlit run app.py
```

---

## 🎬 Quick Start

### 1. Register a New Account
1. Navigate to http://localhost:8501
2. Click "Register" or go to "📝 Register" page
3. Fill in the registration form:
   - Full name
   - Email address
   - Username
   - Password (meets complexity requirements)
   - Accept terms & conditions
4. Click "Create Account"
5. Copy the verification token (in development mode)

### 2. Verify Email (Development)
In production, users would receive an email. In development:
- The verification token is displayed on the registration success page
- Save this token for later use

### 3. Login
1. Go to "🔐 Login" page
2. Enter email/username and password
3. Check "Remember me" for extended session (optional)
4. Click "Sign In"

### 4. Access Profile
1. Once logged in, navigate to "👤 Profile"
2. View account information
3. Edit profile details
4. Change password
5. View login history

---

## 🏗️ Architecture

### Directory Structure
```
nexus-platform/
├── app.py                          # Main Streamlit application
├── init_db.py                      # Database initialization script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── modules/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── authentication.py       # Login, register, logout logic
│   │   ├── authorization.py        # RBAC implementation
│   │   ├── session_manager.py      # Streamlit session management
│   │   ├── password_utils.py       # Password hashing & validation
│   │   ├── oauth.py                # OAuth integration
│   │   └── middleware.py           # Auth decorators
│   └── database/
│       ├── __init__.py
│       ├── models.py               # SQLAlchemy models
│       └── connection.py           # Database connection
└── pages/
    ├── 1_🔐_Login.py               # Login page
    ├── 2_📝_Register.py            # Registration page
    ├── 3_👤_Profile.py             # User profile page
    └── 4_🔑_Reset_Password.py      # Password reset page
```

### Database Schema

#### Users Table
- `id`: Primary key
- `email`: Unique email address
- `username`: Unique username
- `full_name`: User's full name
- `hashed_password`: Bcrypt hashed password
- `avatar_url`: Profile picture URL
- `is_active`: Account active status
- `is_verified`: Email verification status
- `is_locked`: Account lockout status
- `oauth_provider`: OAuth provider (google, microsoft)
- `oauth_id`: OAuth user ID
- `failed_login_attempts`: Failed login counter
- `last_login`: Last successful login timestamp
- `created_at`: Account creation timestamp

#### Roles Table
- `id`: Primary key
- `name`: Role name (admin, manager, user, guest)
- `description`: Role description

#### Permissions Table
- `id`: Primary key
- `name`: Permission name (e.g., user.create)
- `description`: Permission description
- `module`: Module this permission applies to

#### User Sessions Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `session_token`: JWT access token
- `refresh_token`: JWT refresh token
- `ip_address`: Client IP
- `user_agent`: Client user agent
- `remember_me`: Remember me flag
- `expires_at`: Session expiration
- `created_at`: Session creation timestamp

#### Login History Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `success`: Login success flag
- `ip_address`: Client IP
- `user_agent`: Client user agent
- `failure_reason`: Reason for failure
- `created_at`: Login attempt timestamp

---

## 📖 Usage Guide

### For Developers

#### Protecting a Page
```python
import streamlit as st
from modules.auth import StreamlitSessionManager

# Require authentication
StreamlitSessionManager.require_auth()

# Your protected page code here
st.write("This is a protected page")
```

#### Require Specific Role
```python
from modules.auth import StreamlitSessionManager

# Require admin role
StreamlitSessionManager.require_role("admin")

# Or require any of multiple roles
StreamlitSessionManager.require_any_role(["admin", "manager"])
```

#### Using Decorators
```python
from modules.auth.middleware import require_auth, require_role

@require_auth()
def protected_function():
    st.write("Only authenticated users can see this")

@require_role("admin")
def admin_function():
    st.write("Only admins can see this")

@require_any_role(["admin", "manager"])
def manager_function():
    st.write("Admins and managers can see this")
```

#### Get Current User
```python
from modules.auth import StreamlitSessionManager

user = StreamlitSessionManager.get_current_user()
if user:
    st.write(f"Hello, {user['full_name']}")
    st.write(f"Email: {user['email']}")
    st.write(f"Roles: {user['roles']}")
```

#### Check Permissions
```python
from modules.auth import StreamlitSessionManager

# Check if user is admin
if StreamlitSessionManager.is_admin():
    st.write("Admin controls")

# Check if user is manager or admin
if StreamlitSessionManager.is_manager():
    st.write("Manager controls")

# Check specific role
if StreamlitSessionManager.has_role("user"):
    st.write("User content")
```

#### Show/Hide UI Based on Roles
```python
from modules.auth.middleware import show_for_roles

@show_for_roles(["admin"])
def admin_button():
    if st.button("Admin Action"):
        # Admin-only action
        pass

# Call the function
admin_button()
```

### For End Users

#### Registration
1. Click "Register" from the home page
2. Fill in all required fields
3. Create a strong password (requirements shown)
4. Accept terms & conditions
5. Verify your email (check inbox)

#### Login
1. Navigate to Login page
2. Enter email or username
3. Enter password
4. (Optional) Check "Remember me"
5. Click "Sign In"

#### Password Reset
1. Click "Forgot password?" on login page
2. Enter your email address
3. Check your email for reset link
4. Click the link and enter new password
5. Login with new password

#### Profile Management
1. Go to Profile page
2. View account overview and statistics
3. Edit profile information
4. Change password
5. View login history

---

## 🔐 Security

### Password Requirements
- Minimum 8 characters (recommended 12+)
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character
- Not a common password

### Security Best Practices

1. **Environment Variables**
   - Never commit `.env` file
   - Use strong SECRET_KEY in production
   - Rotate keys regularly

2. **Database**
   - Use PostgreSQL/MySQL in production (not SQLite)
   - Enable SSL connections
   - Regular backups
   - Limit database user permissions

3. **OAuth**
   - Store credentials in environment variables
   - Use HTTPS redirect URIs in production
   - Validate OAuth state parameter

4. **Sessions**
   - Configure appropriate timeout
   - Clear sessions on logout
   - Implement session rotation

5. **Deployment**
   - Use HTTPS in production
   - Set secure cookie flags
   - Enable CSRF protection
   - Implement rate limiting
   - Regular security updates

---

## ⚙️ Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./nexus_platform.db

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Security
MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
SESSION_TIMEOUT_MINUTES=60

# OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

### Database Configuration

#### SQLite (Development)
```python
DATABASE_URL=sqlite:///./nexus_platform.db
```

#### PostgreSQL (Production)
```python
DATABASE_URL=postgresql://user:password@localhost/nexus_platform
```

#### MySQL (Production)
```python
DATABASE_URL=mysql://user:password@localhost/nexus_platform
```

---

## 🛠️ Development

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

### Database Migrations
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## 📝 License

© 2024 NEXUS Platform. All rights reserved.

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Contact: support@nexusplatform.com

---

**Built with ❤️ using Streamlit, SQLAlchemy, and Python**

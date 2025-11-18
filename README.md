# 🚀 NEXUS Platform

**Unified AI-Powered Productivity Suite**

NEXUS is an all-in-one productivity platform that brings together essential business tools in a unified, intelligent workspace. Built with Streamlit and powered by Claude AI, NEXUS provides a seamless experience across 8 core applications.

## 📋 Table of Contents

- [Features](#features)
- [Applications](#applications)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [AI Features](#ai-features)
- [Export Capabilities](#export-capabilities)
- [Development](#development)
- [License](#license)

## ✨ Features

- **8 Integrated Applications** - PowerPoint, Email, Chat, Projects, Calendar, Video Conference, Notes, CRM
- **AI-Powered** - Claude AI integration for intelligent assistance
- **Modern UI** - Built with Streamlit for responsive, intuitive interfaces
- **Database Integration** - SQLAlchemy ORM with SQLite backend
- **Export Capabilities** - PDF, PPTX, DOCX, XLSX, ICS, MD formats
- **Real-time Collaboration** - Chat and messaging features
- **Project Management** - Gantt charts, Kanban boards, dependencies
- **Contact Management** - Full-featured CRM with pipeline visualization

## 📱 Applications

### 1. 📊 PowerPoint / Presentation Editor

Create professional presentations with AI assistance.

**Features:**
- Slide editor with multiple layouts
- Theme customization
- AI content generation
- Export to PPTX and PDF
- Speaker notes
- Slide reordering

**AI Features:**
- Generate presentation content from topics
- Auto-create slides with structured content
- Smart content suggestions

### 2. 📧 Email Client

Smart email management with threading and AI replies.

**Features:**
- Inbox, Sent, Drafts, Starred folders
- Email categorization (Primary, Social, Promotions, etc.)
- Rich text composition
- Email threading
- Search and filters
- Attachments support

**AI Features:**
- Smart reply generation
- Email sentiment analysis
- Context-aware suggestions

### 3. 💬 Chat / Messaging

Real-time team communication and collaboration.

**Features:**
- Public and private chat rooms
- Direct messaging
- File sharing
- Emoji reactions
- Message search
- Member management
- Auto-refresh option

### 4. 📊 Projects / Task Management

Comprehensive project management with multiple views.

**Features:**
- Kanban board view
- Gantt chart visualization
- Task list with dependencies
- Milestones tracking
- Progress monitoring
- Team assignment
- Budget tracking
- Export to Excel

**AI Features:**
- Auto-generate tasks from project description
- Smart dependency suggestions
- Project insights

### 5. 📅 Calendar

Multi-view calendar with smart scheduling.

**Features:**
- Day, Week, Month views
- Event creation and management
- Recurring events
- Event reminders
- Attendee management
- Multiple event types
- Export to ICS format

**AI Features:**
- Meeting agenda generation
- Smart scheduling suggestions

### 6. 📹 Video Conference

Virtual meeting platform with recording.

**Features:**
- Conference scheduling
- Participant management
- Recording capabilities
- Screen sharing (placeholder)
- Meeting controls
- Conference history

**AI Features:**
- Meeting summary generation
- Auto-transcription (planned)

### 7. 📝 Notes

Rich note-taking with organization and AI summaries.

**Features:**
- Rich text editing (Markdown support)
- Folder organization
- Tag system
- Search functionality
- Color coding
- Favorites and archives
- Export to PDF, DOCX, MD

**AI Features:**
- Automatic summarization
- Smart tagging suggestions
- Content expansion

### 8. 💼 CRM (Customer Relationship Management)

Complete contact and deal management system.

**Features:**
- Contact management
- Deal pipeline visualization
- Activity tracking
- Contact types and segmentation
- Deal stages and probability
- Export to Excel
- Search and filtering

**AI Features:**
- Next step suggestions
- Lead qualification
- Email drafting assistance

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd nexus-platform
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Initialize database:**
   ```bash
   python -c "from database.connection import init_db; init_db()"
   ```

5. **Run the application:**
   ```bash
   streamlit run Home.py
   ```

The application will be available at `http://localhost:8501`

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```env
# AI Configuration
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Database
DATABASE_URL=sqlite:///nexus.db

# Application
ENVIRONMENT=development
SECRET_KEY=your-secret-key

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password

# Features
ENABLE_AI_FEATURES=true
ENABLE_EXPORT=true
ENABLE_FILE_SHARING=true

# Limits
MAX_FILE_SIZE_MB=100
```

## 📖 Usage

### Starting the Application

```bash
streamlit run Home.py
```

### Navigating the Platform

1. **Home Page** - Overview and quick stats
2. **Sidebar Navigation** - Access all 8 applications
3. **Application Pages** - Each app has its own dedicated interface

### Common Workflows

#### Creating a Presentation
1. Navigate to PowerPoint app
2. Click "New Presentation"
3. Add slides manually or use AI generation
4. Customize themes and content
5. Export to PPTX or PDF

#### Managing Projects
1. Go to Projects app
2. Create new project
3. Add tasks and milestones
4. View in Kanban or Gantt chart
5. Track progress and dependencies

#### Taking Notes
1. Open Notes app
2. Create new note
3. Write content with Markdown support
4. Organize with folders and tags
5. Generate AI summary
6. Export in preferred format

## 🏗️ Architecture

### Project Structure

```
nexus-platform/
├── Home.py                      # Main entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── config/                      # Configuration
│   ├── settings.py             # App settings
│   └── constants.py            # Constants
├── database/                    # Database layer
│   ├── connection.py           # DB connection
│   └── models.py               # SQLAlchemy models
├── ai/                         # AI integration
│   ├── claude_client.py        # Claude API wrapper
│   └── prompts.py              # Prompt templates
├── utils/                      # Utilities
│   ├── exporters.py           # Export functions
│   ├── validators.py          # Input validation
│   └── formatters.py          # Data formatting
├── apps/                       # Applications
│   ├── powerpoint/
│   ├── email/
│   ├── chat/
│   ├── projects/
│   ├── calendar/
│   ├── video_conference/
│   ├── notes/
│   └── crm/
└── pages/                      # Streamlit pages
    ├── 1_📊_PowerPoint.py
    ├── 2_📧_Email.py
    └── ...
```

### Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite with SQLAlchemy ORM
- **AI**: Anthropic Claude API
- **Visualization**: Plotly, Matplotlib
- **Export**: ReportLab, python-pptx, python-docx, openpyxl

## 🤖 AI Features

NEXUS integrates Claude AI throughout the platform:

### Content Generation
- Presentation slides from topics
- Email replies with context
- Meeting agendas
- Task lists from descriptions

### Analysis & Insights
- Email sentiment analysis
- Note summarization
- Project insights
- CRM next steps

### Smart Assistance
- Content improvement suggestions
- Dependency analysis
- Lead qualification
- Scheduling optimization

## 📤 Export Capabilities

### Supported Formats

- **PDF** - Universal document format
- **PPTX** - PowerPoint presentations
- **DOCX** - Word documents
- **XLSX** - Excel spreadsheets
- **ICS** - Calendar events
- **MD** - Markdown files
- **HTML** - Web format (emails)

### Export Features

- One-click export from any application
- Preserves formatting and structure
- Download directly to local machine
- Batch export capabilities

## 🛠️ Development

### Adding a New Application

1. Create app directory in `apps/`
2. Implement `main.py` with Streamlit UI
3. Add database models to `database/models.py`
4. Create page entry in `pages/`
5. Update Home.py with app info

### Database Migrations

```python
from database.connection import init_db
init_db()  # Creates all tables
```

### Testing

```bash
# Run with test data
ENVIRONMENT=development streamlit run Home.py
```

## 📝 License

[Add your license here]

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please open an issue on GitHub.

## 🎯 Roadmap

- [ ] Real WebRTC implementation for video conferencing
- [ ] Advanced rich text editor for notes
- [ ] Email server integration (IMAP/SMTP)
- [ ] Mobile responsive design
- [ ] Multi-user support with authentication
- [ ] Cloud storage integration
- [ ] Advanced analytics dashboard
- [ ] Plugin system for extensions

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Claude AI](https://www.anthropic.com/)
- Uses [SQLAlchemy](https://www.sqlalchemy.org/)
- Visualization by [Plotly](https://plotly.com/)

---

**Built with ❤️ using Streamlit and Claude AI**

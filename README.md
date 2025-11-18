# 🚀 NEXUS Platform

> Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## 📝 Word Editor Module (v1.0.0)

The first module in the NEXUS suite - a comprehensive AI-powered word processor with rich text editing, collaborative features, and intelligent writing assistance.

### ✨ Features

#### 🎨 Rich Text Editing
- **Formatting Options**: Bold, italic, underline
- **Font Control**: Multiple fonts (Arial, Times New Roman, Calibri, etc.)
- **Font Sizes**: 8pt to 72pt
- **Text Colors**: 12 pre-defined colors
- **Alignment**: Left, center, right, justify
- **Headings**: H1-H6 with predefined styles

#### 📊 Content Elements
- **Lists**: Bullet and numbered lists
- **Tables**: Insert custom tables with configurable rows/columns
- **Images**: Insert images with alt text
- **Links**: Add hyperlinks with custom text
- **Undo/Redo**: Full editing history

#### 🤖 AI-Powered Features
- **Grammar Check**: Powered by LanguageTool and Claude AI
- **Spell Check**: Real-time spelling corrections
- **Writing Assistant**: Get suggestions to improve your writing
- **Summarization**: Generate concise summaries
- **Text Expansion**: Elaborate on ideas with AI
- **Tone Adjustment**: Professional, casual, or formal tones
- **Autocomplete**: AI-powered text continuation
- **Outline Generation**: Create structured document outlines
- **Title Generation**: Auto-generate titles from content
- **Keyword Extraction**: Identify key topics
- **Readability Analysis**: Assess document complexity

#### 📈 Document Statistics
- **Word Count**: Real-time word counting
- **Character Count**: With/without spaces
- **Reading Time**: Estimated reading time
- **Version Tracking**: Track document versions

#### 💾 Export & Import
- **Export Formats**: PDF, DOCX, HTML, Markdown, JSON
- **Import Formats**: DOCX, TXT, Markdown, HTML
- **Print Preview**: Ready for printing
- **Auto-save**: Automatic version saving

#### 👥 Collaborative Features
- **Real-time Cursors**: See where others are editing
- **Comments**: Add comments at specific positions
- **Suggestions**: Track changes with accept/reject
- **Version History**: Full version control with diff view
- **User Tracking**: Monitor active collaborators

#### 📋 Document Templates
- Blank Document
- Business Letter
- Resume
- Report
- Meeting Notes
- Project Proposal
- Essay
- Cover Letter

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip
- Anthropic API key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nexus-platform.git
   cd nexus-platform
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Access the application**
   Open your browser to `http://localhost:8501`

## 🔑 API Configuration

To use AI features, you need an Anthropic API key:

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Add to `.env` file:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

## 📁 Project Structure

```
nexus-platform/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── config/                    # Configuration files
│   ├── settings.py           # Application settings
│   └── constants.py          # Constants and configurations
├── core/                      # Core utilities
│   ├── api_client.py         # Claude API client
│   ├── utils.py              # Utility functions
│   └── logging.py            # Logging configuration
├── modules/                   # Feature modules
│   ├── base_module.py        # Abstract base class
│   └── word/                 # Word Editor module
│       ├── module.py         # Main module class
│       ├── ui.py             # UI components
│       ├── document.py       # Document handling
│       ├── ai_features.py    # AI integrations
│       ├── templates.py      # Document templates
│       └── collab.py         # Collaborative features
├── assets/                    # Static assets
│   ├── icons/                # Icons and images
│   └── templates/            # Document templates
└── tests/                     # Test files
```

## 🎯 Usage Guide

### Creating a New Document

1. Click "➕ New Document" in the sidebar
2. Enter a document title
3. Choose a template or start from blank
4. Start typing in the editor

### Using AI Features

1. Write or select text
2. Open the "🤖 AI Assistant" panel in sidebar
3. Choose an AI feature:
   - Grammar Check
   - Summarize
   - Expand Text
   - Adjust Tone
   - etc.
4. Click "✨ Apply AI Feature"
5. Review and apply suggestions

### Exporting Documents

1. Click "💾 Export" in sidebar
2. Choose format (PDF, DOCX, HTML, Markdown)
3. Click "⬇️ Download"
4. Save the file

### Collaborating

1. Go to "👥 Collaboration" tab
2. Enter your name and choose a cursor color
3. Click "Join Session"
4. See other users' cursors and edits in real-time

### Version History

1. Click "📌 Save Version" to create a checkpoint
2. Go to "🕐 History" tab
3. View all versions
4. Click "View Diff" to see changes
5. Click "Restore" to revert to a previous version

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

## 📚 Technologies Used

- **Streamlit**: Web application framework
- **Anthropic Claude**: AI language model
- **python-docx**: DOCX file handling
- **ReportLab**: PDF generation
- **LanguageTool**: Grammar checking
- **Markdown**: Text formatting
- **difflib**: Version comparison

## 🗺️ Roadmap

### Current Release (v1.0.0)
- ✅ Word Editor with AI features
- ✅ Rich text editing
- ✅ Export to multiple formats
- ✅ Collaborative features
- ✅ Version history

### Coming Soon
- 📊 Excel Analyzer
- 📊 PowerPoint Creator
- 📄 PDF Manager
- 🏗️ Project Manager
- 📧 Email Client
- 💬 AI Chat Assistant
- 🔀 Flowchart Designer
- 📈 Analytics Dashboard
- 📅 Meeting Scheduler
- ...and 15 more modules!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Claude AI](https://www.anthropic.com/)
- Grammar checking by [LanguageTool](https://languagetool.org/)

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: support@nexus-platform.com

---

**Made with ❤️ for productivity enthusiasts**

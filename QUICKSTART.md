<<<<<<< HEAD
# Quick Start Guide - Nexus Platform

Get started with Nexus Platform in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- OR Python 3.11+ and Redis installed locally

## Quick Start with Docker (Recommended)

### 1. Setup

```bash
# Clone the repository
git clone <repository-url>
cd nexus-platform

# Copy environment file
cp .env.example .env
```

### 2. Configure (Optional)

Edit `.env` file if you want to add:
- Email settings (SMTP)
- AI API keys (Anthropic, OpenAI)

```bash
nano .env  # or use your preferred editor
```

### 3. Start Everything

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Access Applications

- **Streamlit App**: http://localhost:8501
- **Flower Dashboard**: http://localhost:5555

### 5. Test It Out

1. Open http://localhost:8501
2. Go to **Task Monitor** page
3. Click **Test Health Check** button
4. See the task appear in the queue!

## Quick Start - Local Development

### 1. Install Redis

**macOS**:
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure

```bash
# Copy environment file
cp .env.example .env

# Edit if needed
nano .env
```

### 4. Start Services

**Terminal 1 - Celery Workers**:
```bash
./celery_worker.sh
```

**Terminal 2 - Streamlit App**:
=======
# 🚀 NEXUS Platform - Quick Start Guide

Get up and running with NEXUS Word Editor in 5 minutes!

## Step 1: Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

## Step 2: Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# Get your key from: https://console.anthropic.com/
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

## Step 3: Run the Application

>>>>>>> origin/claude/word-editor-module-01PPyUEeNUgZmU4swtfxgoCB
```bash
streamlit run app.py
```

<<<<<<< HEAD
**Terminal 3 - Flower (Optional)**:
```bash
celery -A config.celery_config flower
```

### 5. Access

- **Streamlit**: http://localhost:8501
- **Flower**: http://localhost:5555

## Testing the System

### Test Email Task

```python
from app.tasks.email_tasks import send_notification

task = send_notification.delay(
    user_email="test@example.com",
    notification_type="task_complete",
    context={'task_name': 'Test', 'details': 'Success'}
)

print(f"Task ID: {task.id}")
```

### Test File Processing

```python
from app.tasks.file_tasks import process_word_document

task = process_word_document.delay(
    file_path="/path/to/document.docx",
    operations=["extract_text", "count_stats"]
)

result = task.get()  # Wait for result
print(result)
```

### Test AI Task

```python
from app.tasks.ai_tasks import claude_completion

task = claude_completion.delay(
    prompt="Write a haiku about programming",
    max_tokens=100
)

result = task.get()
print(result['content'])
```

## Common Commands

### Docker

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Rebuild after code changes
docker-compose build
docker-compose up -d
```

### Celery

```bash
# Check active workers
celery -A config.celery_config inspect active

# Check registered tasks
celery -A config.celery_config inspect registered

# Purge all tasks
celery -A config.celery_config purge
```

### Monitoring

```bash
# Redis CLI
redis-cli

# Check queue lengths
redis-cli LLEN email_queue
redis-cli LLEN ai_queue
```

## Troubleshooting

### Workers not starting?

```bash
# Check Redis
redis-cli ping  # Should return PONG

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check logs
docker-compose logs celery_worker
```

### Tasks not processing?

1. Check workers are running
2. Verify queue names match
3. Check Redis connection
4. Look at Flower dashboard

### Port already in use?

Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Use 8502 instead of 8501
```

## Next Steps

1. **Configure AI**: Add your Anthropic/OpenAI API keys to `.env`
2. **Setup Email**: Configure SMTP settings for email tasks
3. **Explore Tasks**: Check out the different task types in `app/tasks/`
4. **Read Docs**: See `README.md` and `CELERY_SETUP.md` for details
5. **Customize**: Add your own tasks and workflows

## Support

- **Documentation**: See `README.md`
- **Celery Guide**: See `CELERY_SETUP.md`
- **Issues**: Open an issue on GitHub

Happy coding! 🚀
=======
The application will open in your browser at `http://localhost:8501`

## Step 4: Try These Features

### Create Your First Document

1. **Select Word Editor** from the sidebar
2. **Enter a title** in the "Document Title" field
3. **Choose a template** or start from blank:
   - Try "Business Letter" for a professional letter
   - Try "Resume" for a CV template
   - Try "Report" for a structured report

### Use AI Features

1. **Write some text** in the editor
2. **Select an AI feature** from the sidebar:
   - **Grammar Check**: Find and fix grammar errors
   - **Summarize**: Get a concise summary
   - **Expand Text**: Add more details
   - **Adjust Tone**: Change to professional/casual/formal
3. **Click "Apply AI Feature"** to see suggestions

### Export Your Document

1. **Click "Export"** in the sidebar
2. **Choose a format**:
   - PDF for sharing
   - DOCX for editing in Word
   - HTML for web
   - Markdown for documentation
3. **Click "Download"** to save

## 🎯 Key Features to Explore

### Rich Text Editing
- Use the formatting toolbar to style your text
- Choose fonts, sizes, and colors
- Add headings (H1-H6)
- Apply bold, italic, underline

### Insert Elements
- **Tables**: Click "📊 Table" to insert a table
- **Images**: Click "🖼️ Image" and enter a URL
- **Links**: Click "🔗 Link" to add hyperlinks

### Version History
1. Click "📌 Save Version" to create a checkpoint
2. Go to "🕐 History" tab to see all versions
3. Click "View Diff" to see what changed
4. Click "Restore" to go back to a previous version

### Comments & Collaboration
1. Go to "💬 Comments" tab
2. Add comments at specific positions
3. Resolve comments when addressed
4. Go to "👥 Collaboration" to simulate multi-user editing

## 📊 Document Statistics

Watch the real-time statistics at the bottom of the editor:
- **Word Count**: Total words
- **Character Count**: Total characters
- **Reading Time**: Estimated time to read
- **Version**: Current version number

## 🎨 Formatting Tips

### Markdown Support
The editor supports Markdown formatting:

```markdown
# Heading 1
## Heading 2
### Heading 3

**Bold text**
*Italic text*

- Bullet point 1
- Bullet point 2

1. Numbered item 1
2. Numbered item 2

[Link text](https://example.com)

![Image alt text](https://example.com/image.jpg)
```

### Tables
Insert a table and format it like this:

```markdown
| Column 1 | Column 2 | Column 3 |
| -------- | -------- | -------- |
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

## 🤖 AI Feature Examples

### Grammar Check
**Input:** "I has been working on this project yesterday."
**Output:** Corrects to "I was working on this project yesterday."

### Summarize
**Input:** A long article or document
**Output:** A concise 2-3 sentence summary

### Tone Adjustment
**Input:** "Hey, can you send me that report?"
**Professional:** "Could you please send me the report?"
**Formal:** "I would appreciate it if you could provide me with the report."

### Create Outline
**Input:** "Write a blog post about productivity tips"
**Output:**
```
I. Introduction
   A. Importance of productivity
   B. Overview of tips

II. Time Management
   A. Prioritization
   B. Time blocking
   ...
```

## ⚙️ Customization

### Change Theme
Edit `.streamlit/config.toml` to customize colors:

```toml
[theme]
primaryColor="#4F46E5"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F3F4F6"
```

### Auto-save Settings
- Toggle "💾 Auto-save" in the sidebar
- When enabled, versions are saved automatically on every edit

## 🐛 Troubleshooting

### "API key not configured" Error
- Make sure you've added your Anthropic API key to the `.env` file
- Restart the application after adding the key
- Or enter the key in the UI (temporary for session)

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using Python 3.8 or higher: `python --version`

### Port Already in Use
- Change the port: `streamlit run app.py --server.port 8502`
- Or kill the existing process

### LanguageTool Download
- First time using grammar check may take a moment to download LanguageTool
- Requires internet connection

## 📚 Next Steps

1. **Explore Templates**: Try different document templates
2. **Test AI Features**: Experiment with all AI capabilities
3. **Collaborate**: Try the collaboration features
4. **Export Options**: Test different export formats
5. **Version Control**: Practice with version history

## 💡 Tips & Tricks

- **Keyboard Shortcuts**: Use standard text editing shortcuts (Ctrl+C, Ctrl+V, etc.)
- **Save Often**: Use "Save Version" before major changes
- **Comment Wisely**: Add comments to track discussion points
- **Templates**: Start with templates to save time
- **AI Assistance**: Use AI features iteratively for best results

## 🎓 Learning Resources

- **README.md**: Full documentation
- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **Claude AI**: [anthropic.com/claude](https://www.anthropic.com/claude)

## 🆘 Getting Help

- Check the [README.md](README.md) for detailed documentation
- Open an issue on GitHub
- Review example documents in `assets/templates/`

---

**Ready to be productive? Start creating amazing documents with NEXUS! 🚀**
>>>>>>> origin/claude/word-editor-module-01PPyUEeNUgZmU4swtfxgoCB

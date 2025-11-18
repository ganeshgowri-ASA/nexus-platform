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

```bash
streamlit run app.py
```

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

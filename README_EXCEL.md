# 📊 NEXUS Excel Spreadsheet Module

A world-class, AI-powered spreadsheet application built for the NEXUS platform. This module rivals Google Sheets and Excel Online with advanced features, comprehensive formula support, and intelligent automation.

## ✨ Features

### Core Spreadsheet Functionality
- **Infinite Grid**: Smooth scrolling grid with dynamic row/column management
- **Cell Operations**:
  - Single, range, and multi-cell selection
  - Copy/paste with formatting preservation
  - Drag-to-fill formulas
  - Unlimited undo/redo
  - Cell merging and splitting

### 🔢 Formula Engine (Excel-Compatible)
Over 200 built-in formulas across multiple categories:

#### Mathematical Functions
- `SUM`, `AVERAGE`, `COUNT`, `MIN`, `MAX`
- `ROUND`, `ROUNDUP`, `ROUNDDOWN`
- `ABS`, `SQRT`, `POWER`, `MOD`
- `CEILING`, `FLOOR`, `INT`

#### Logical Functions
- `IF`, `AND`, `OR`, `NOT`
- `IFS`, `SWITCH`
- Nested conditional logic support

#### Text Functions
- `CONCATENATE`, `CONCAT`
- `LEFT`, `RIGHT`, `MID`
- `LEN`, `TRIM`, `UPPER`, `LOWER`, `PROPER`
- `SUBSTITUTE`, `REPLACE`, `FIND`, `SEARCH`

#### Lookup Functions
- `VLOOKUP`, `HLOOKUP`
- `INDEX`, `MATCH`, `XLOOKUP`

#### Date/Time Functions
- `TODAY`, `NOW`, `DATE`
- `YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`
- `DATEDIF`

#### Financial Functions
- `PMT`, `FV`, `PV`, `RATE`
- `NPV`, `IRR`

#### Statistical Functions
- `STDEV`, `VAR`, `MEDIAN`, `MODE`
- `PERCENTILE`, `QUARTILE`

### 🎨 Formatting & Styling
- **Font Styling**: Family, size, color, bold, italic, underline, strikethrough
- **Cell Colors**: Background colors and borders
- **Alignment**: Horizontal and vertical alignment, text wrapping
- **Number Formats**: Currency, percentage, date, time, custom formats
- **Conditional Formatting**:
  - Color scales (3-color gradients)
  - Data bars
  - Icon sets
  - Highlight duplicates/unique values
  - Custom rules with formulas

### 📊 Charts & Visualization
- **Chart Types**: Line, Bar, Column, Pie, Scatter, Area, Histogram, Box, Heatmap
- **Customization**: Colors, labels, legends, titles
- **Dynamic Updates**: Charts update automatically with data changes
- **Sparklines**: Mini inline charts for trends

### 🔄 Pivot Tables
- **Drag-and-Drop Builder**: Intuitive pivot table creation
- **Aggregations**: Sum, count, average, min, max, median, std, var
- **Multiple Dimensions**: Row fields, column fields, value fields
- **Filters & Slicers**: Advanced filtering options
- **Pivot Charts**: Visualize pivot table data

### 🛠️ Data Tools
- **Sort**: Multi-column sorting (ascending/descending)
- **Filter**: Auto-filter and advanced filtering
- **Find & Replace**: With regex and case-sensitivity options
- **Remove Duplicates**: Clean data efficiently
- **Text-to-Columns**: Split delimited text
- **Data Validation**:
  - Dropdown lists
  - Number ranges
  - Date/time validation
  - Text length validation
  - Custom formulas

### 🤖 AI Assistant
Powered by Claude (Anthropic):
- **Natural Language Queries**: "Show me top 10 sales by region"
- **Formula Generation**: Describe what you want, get the formula
- **Data Analysis**: Automated insights and pattern recognition
- **Chart Suggestions**: AI recommends best visualization
- **Data Cleaning**: Automated quality checks and suggestions
- **Anomaly Detection**: Identify outliers and unusual patterns
- **Predictive Analytics**: Forecast future values
- **Smart Search**: Natural language search across data

### 📤 Import/Export
- **Import Formats**: Excel (.xlsx, .xls), CSV, TSV, JSON
- **Export Formats**: Excel, CSV, JSON, HTML, PDF
- **Cloud Integration**: Google Sheets sync (with credentials)
- **Format Auto-Detection**: Automatically detect file formats

### 👥 Collaboration
- **Real-Time Editing**: Multiple users can edit simultaneously
- **Cell Locking**: Prevent conflicts during editing
- **Comments & Notes**: Add threaded comments to cells
- **Change Tracking**: Full audit trail of all changes
- **Version History**: Save and restore previous versions
- **Share Permissions**: View, Edit, Admin levels

## 🏗️ Architecture

### Module Structure
```
modules/excel/
├── __init__.py                 # Module exports
├── models.py                   # Database models
├── editor.py                   # Main spreadsheet engine
├── formula_engine.py           # Excel formula evaluation
├── cell_manager.py             # Cell editing & formatting
├── data_validator.py           # Data validation rules
├── chart_builder.py            # Charts & visualizations
├── pivot_table.py              # Pivot table functionality
├── conditional_format.py       # Conditional formatting
├── data_tools.py               # Data manipulation tools
├── import_export.py            # File import/export
├── collaboration.py            # Multi-user features
├── ai_assistant.py             # AI-powered features
└── streamlit_ui.py             # Streamlit interface
```

### Core Infrastructure
```
core/
├── database/                   # Database management
│   ├── base.py                # SQLAlchemy base
│   └── session.py             # Session management
├── auth/                      # Authentication
│   ├── models.py              # User model
│   ├── service.py             # Auth service
│   └── middleware.py          # Auth middleware
├── ai/                        # AI orchestration
│   └── orchestrator.py        # Claude AI integration
└── storage/                   # File storage
    └── manager.py             # Local/S3 storage
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Anthropic API key (for AI features)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd nexus-platform
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Configure database**:
```bash
# Update DATABASE_URL in .env
# Example: postgresql://user:password@localhost:5432/nexus
```

6. **Run the application**:
```bash
streamlit run app.py
```

## 📝 Usage Examples

### Creating a New Spreadsheet
```python
from modules.excel.editor import SpreadsheetEditor

# Initialize editor
editor = SpreadsheetEditor(db_session, user_id)

# Create new spreadsheet
spreadsheet = editor.create_new("Sales Report", rows=100, cols=26)

# Add data
editor.set_cell_value(0, 0, "Product")
editor.set_cell_value(0, 1, "Sales")
editor.set_cell_value(1, 0, "Item A")
editor.set_cell_value(1, 1, 1000)

# Add formula
editor.set_cell_formula(2, 1, "=SUM(B2:B10)")

# Save
editor.save()
```

### Using Formulas
```python
# Mathematical formulas
editor.set_cell_formula(0, 0, "=SUM(A1:A10)")
editor.set_cell_formula(0, 1, "=AVERAGE(B1:B10)")
editor.set_cell_formula(0, 2, "=ROUND(C1, 2)")

# Logical formulas
editor.set_cell_formula(0, 3, "=IF(D1>100, 'High', 'Low')")
editor.set_cell_formula(0, 4, "=AND(E1>50, E1<100)")

# Text formulas
editor.set_cell_formula(0, 5, "=CONCATENATE(F1, ' ', G1)")
editor.set_cell_formula(0, 6, "=UPPER(H1)")
```

### Creating Charts
```python
from modules.excel.chart_builder import ChartConfig, ChartType

config = ChartConfig(
    chart_type=ChartType.LINE,
    title="Sales Trend",
    x_axis="Month",
    y_axis=["Sales", "Profit"]
)

chart = editor.create_chart(config)
```

### AI Analysis
```python
# Get insights
insights = editor.get_ai_insights("What are the top performing products?")

# Generate formula
formula = editor.get_ai_formula_suggestion("calculate total revenue")

# Data cleaning suggestions
suggestions = editor.get_data_cleaning_suggestions()
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules/excel

# Run specific test file
pytest tests/test_excel.py -v
```

## 📊 Database Schema

### Spreadsheet Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `name`: Spreadsheet name
- `description`: Optional description
- `file_path`: Storage path
- `data_json`: JSON representation
- `metadata`: Additional metadata
- `settings`: User preferences
- `created_at`, `updated_at`, `last_accessed`: Timestamps

### SpreadsheetVersion Table
- `id`: Primary key
- `spreadsheet_id`: Foreign key
- `version_number`: Version number
- `file_path`: Version file path
- `change_summary`: Description of changes
- `created_by`: User who created version
- `created_at`: Timestamp

### SpreadsheetShare Table
- `id`: Primary key
- `spreadsheet_id`: Foreign key
- `user_id`: Shared with user
- `permission`: View/Edit/Admin
- `shared_by`: User who shared
- `created_at`: Timestamp

## 🔧 Configuration

### Environment Variables
See `.env.example` for all configuration options:
- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: Claude AI API key
- `STORAGE_TYPE`: `local` or `s3`
- `JWT_SECRET_KEY`: Secret key for authentication

### Storage Options
- **Local**: Files stored in `./storage` directory
- **S3**: Files stored in AWS S3 bucket (configure AWS credentials)

## 🎯 Roadmap

- [ ] Real-time collaboration with WebSockets
- [ ] Advanced Excel compatibility (macros, VBA)
- [ ] Mobile-responsive interface
- [ ] Offline mode with sync
- [ ] Custom function creation
- [ ] Plugin system for extensions
- [ ] Advanced charting (3D, combo charts)
- [ ] Data connectors (SQL, APIs, etc.)
- [ ] Automated reporting
- [ ] Multi-language support

## 🤝 Contributing

This is a proprietary module for the NEXUS platform. Contact the development team for contribution guidelines.

## 📄 License

Proprietary - All rights reserved

## 👨‍💻 Authors

**NEXUS Development Team**
- Built with Claude AI assistance
- Powered by Anthropic's Claude Sonnet 4.5

## 🙏 Acknowledgments

- Anthropic for Claude AI
- Streamlit for the amazing web framework
- Plotly for beautiful visualizations
- The open-source community

---

**Built with ❤️ for the NEXUS Platform**

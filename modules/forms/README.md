# 📋 NEXUS Forms & Surveys Module

A comprehensive, production-ready form builder and survey platform that rivals Google Forms and Typeform. Built for the NEXUS platform with enterprise-grade features, powerful analytics, and seamless integrations.

## 🌟 Features

### Form Builder
- **Drag & Drop Interface**: Intuitive visual form builder
- **20+ Field Types**: Text, email, phone, dropdown, checkbox, radio, file upload, date, rating, matrix, NPS, and more
- **Multi-Page Forms**: Break long forms into multiple pages with progress tracking
- **Field Validation**: Required fields, regex patterns, min/max values, custom rules
- **Custom Branding**: Themes, custom CSS, logo upload, color customization

### Conditional Logic
- **Smart Branching**: Show/hide fields based on user responses
- **Skip Logic**: Jump to specific pages based on answers
- **Calculated Fields**: Automatic calculations based on other field values
- **Answer Piping**: Insert previous answers into questions

### Response Management
- **Real-Time Submissions**: Live response tracking
- **Spreadsheet View**: View responses in table format
- **Advanced Filtering**: Filter by field values, date ranges, and more
- **Search Functionality**: Quickly find specific responses
- **Spam Detection**: Automatic spam and duplicate detection

### Analytics & Insights
- **Completion Rates**: Track form completion and abandonment
- **Time Analysis**: Average completion time, time distribution
- **Drop-off Analysis**: Identify where users abandon the form
- **Field Statistics**: Detailed analytics per field
- **Response Trends**: Daily, weekly, monthly response patterns
- **Device Distribution**: Desktop vs mobile vs tablet usage
- **NPS Scoring**: Net Promoter Score calculations
- **Custom Charts**: Bar, pie, line, and funnel charts

### Data Export
- **Multiple Formats**: CSV, Excel, PDF, JSON
- **Google Sheets Integration**: Direct export to Google Sheets
- **Batch Export**: Export multiple forms at once
- **Scheduled Exports**: Automatic export scheduling
- **Custom Fields Selection**: Choose which fields to export

### Templates Library
- **Pre-Built Templates**:
  - Contact Forms
  - Customer Satisfaction Surveys
  - Event Registration
  - Job Applications
  - Product Feedback
  - Quizzes & Assessments
  - Lead Generation
  - Volunteer Signup

### Distribution
- **Share Links**: Unique URLs for each form
- **Embed Code**: Iframe embed for websites
- **QR Codes**: Generate QR codes for offline sharing
- **Email Distribution**: Send forms via email
- **Access Control**: Public or login-required forms

## 📦 Installation

### Requirements
```bash
pip install streamlit pandas plotly openpyxl reportlab
```

### Optional Dependencies
```bash
# For Google Sheets integration
pip install google-auth google-api-python-client

# For advanced PDF generation
pip install reportlab

# For Excel export
pip install openpyxl
```

## 🚀 Quick Start

### Running the UI

```python
import streamlit as st
from modules.forms.streamlit_ui import FormsUI

# Initialize and render the UI
ui = FormsUI()
ui.render()
```

Or run directly:
```bash
streamlit run modules/forms/streamlit_ui.py
```

### Creating a Form Programmatically

```python
from modules.forms import FormBuilder, FieldFactory

# Create a form builder
builder = FormBuilder()

# Create a new form
form = builder.create_form("Customer Feedback Survey")

# Add fields
form.add_field(FieldFactory.create_email("Email Address", required=True))
form.add_field(FieldFactory.create_rating("How satisfied are you?", max_rating=5))
form.add_field(FieldFactory.create_long_text("Additional Comments"))

# Publish the form
share_link = form.publish()
print(f"Form published at: {share_link}")
```

### Using Templates

```python
from modules.forms.templates import TemplateLibrary

# Get a template
template = TemplateLibrary.get_customer_satisfaction_survey()

# Convert to form
form = template.to_form()

# Customize
form.settings.title = "My Company Customer Survey"
form.settings.primary_color = "#FF5733"
```

### Adding Conditional Logic

```python
from modules.forms.logic import LogicRuleBuilder, ConditionOperator, ActionType

# Create a logic rule
rule = LogicRuleBuilder("Show follow-up if dissatisfied") \
    .add_condition("rating_field", ConditionOperator.LESS_THAN, 3) \
    .add_action(ActionType.SHOW_FIELD, "follow_up_field") \
    .build()

# Add to form
form.logic.add_rule(rule)
```

### Handling Responses

```python
from modules.forms import ResponseManager, FormResponse
from datetime import datetime

# Create response manager
response_mgr = ResponseManager()

# Submit a response
response = FormResponse(
    form_id=form.id,
    data={
        "email": "user@example.com",
        "rating": 5,
        "comments": "Great service!"
    },
    submitted_at=datetime.now(),
    time_spent=120
)

response_id = response_mgr.submit_response(response)

# Get all responses
responses = response_mgr.get_form_responses(form.id)
print(f"Total responses: {len(responses)}")
```

### Analytics

```python
from modules.forms.analytics import FormAnalytics

# Create analytics instance
analytics = FormAnalytics(responses, form.fields)

# Get overview metrics
metrics = analytics.get_overview_metrics()
print(f"Completion Rate: {metrics.completion_rate:.2f}%")
print(f"Average Time: {metrics.average_time:.0f} seconds")

# Get field statistics
stats = analytics.get_field_statistics(field_id)
print(f"Field responses: {stats['total_responses']}")

# Get response trends
trends = analytics.get_response_trends(days=30)
```

### Exporting Data

```python
from modules.forms.export import DataExporter

# Create exporter
exporter = DataExporter(responses, form.fields)

# Export to CSV
csv_content = exporter.export_to_csv("responses.csv")

# Export to Excel
exporter.export_to_excel("responses.xlsx")

# Export to JSON
json_content = exporter.export_to_json("responses.json")

# Export to PDF
exporter.export_to_pdf("responses.pdf")

# Export to Google Sheets
exporter.export_to_google_sheets(
    spreadsheet_id="your-sheet-id",
    credentials_path="credentials.json"
)
```

## 🏗️ Architecture

### Module Structure
```
modules/forms/
├── __init__.py              # Package initialization
├── field_types.py           # 20+ field type definitions
├── validation.py            # Validation rules and validators
├── logic.py                 # Conditional logic engine
├── form_builder.py          # Form builder and management
├── responses.py             # Response handling and storage
├── analytics.py             # Analytics and insights
├── export.py                # Data export functionality
├── templates.py             # Pre-built form templates
├── streamlit_ui.py          # Streamlit UI interface
├── tests/                   # Comprehensive test suite
│   ├── __init__.py
│   ├── test_field_types.py
│   ├── test_validation.py
│   └── test_form_builder.py
└── README.md               # This file
```

### Core Classes

#### Field Types
- `Field`: Base field class with validation
- `FieldType`: Enum of 20+ field types
- `FieldConfig`: Field configuration options
- `FieldFactory`: Factory for creating pre-configured fields

#### Form Builder
- `Form`: Main form class
- `FormBuilder`: Form management and CRUD operations
- `FormSettings`: Form-level configuration
- `FormTheme`: Theming and styling

#### Validation
- `ValidationRule`: Individual validation rule
- `Validator`: Multi-rule validator
- `ValidationRuleBuilder`: Builder pattern for rules
- `CommonValidations`: Pre-built validation sets

#### Conditional Logic
- `Condition`: Single condition definition
- `LogicRule`: Complete logic rule with actions
- `ConditionalLogic`: Logic rule manager
- `BranchingLogic`: Page branching and skip logic
- `Calculator`: Field calculations
- `Piping`: Answer piping functionality

#### Responses
- `FormResponse`: Single response data
- `ResponseManager`: Response CRUD and filtering
- `ResponseValidator`: Spam and duplicate detection
- `ResponseNotifier`: Email notification handling

#### Analytics
- `FormAnalytics`: Main analytics engine
- `AnalyticsMetrics`: Metrics container
- `ChartGenerator`: Chart data generation
- `ReportGenerator`: Report generation

#### Export
- `DataExporter`: Multi-format exporter
- `BatchExporter`: Batch export functionality
- `ExportScheduler`: Scheduled exports

#### Templates
- `FormTemplate`: Template definition
- `TemplateLibrary`: Pre-built templates
- `TemplateCustomizer`: Template customization

## 🎨 UI Features

### Form Builder Interface
- Visual form canvas
- Field palette with drag & drop
- Live preview mode
- Settings panel
- Logic rule builder
- Design customization

### Response Dashboard
- Real-time response list
- Spreadsheet view
- Individual response details
- Filtering and search
- Bulk actions
- Export options

### Analytics Dashboard
- Overview metrics
- Response trends charts
- Field-level statistics
- Drop-off analysis
- Time analysis
- Device distribution
- Custom date ranges

### Templates Gallery
- Category filtering
- Search functionality
- Preview before use
- One-click template loading

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest modules/forms/tests/

# Run specific test file
pytest modules/forms/tests/test_field_types.py -v

# Run with coverage
pytest modules/forms/tests/ --cov=modules/forms --cov-report=html
```

## 📊 Field Types Reference

| Field Type | Description | Use Case |
|------------|-------------|----------|
| Short Text | Single-line text input | Names, titles, short answers |
| Long Text | Multi-line text area | Comments, descriptions |
| Email | Email input with validation | Email addresses |
| Phone | Phone number input | Contact numbers |
| URL | URL input with validation | Website links |
| Number | Numeric input | Ages, quantities, scores |
| Dropdown | Single selection dropdown | Country, state, category |
| Radio | Single choice radio buttons | Yes/No, multiple choice |
| Checkbox | Multiple selection checkboxes | Interests, preferences |
| Multi-Select | Multiple selection dropdown | Tags, categories |
| Date | Date picker | Birthdate, event date |
| Time | Time picker | Appointment time |
| DateTime | Combined date and time | Timestamp |
| File Upload | File upload field | Documents, images |
| Image Upload | Image-specific upload | Photos, logos |
| Rating | Star/heart rating | Satisfaction, quality |
| Scale | Numeric scale | Agreement scale (1-7) |
| NPS | Net Promoter Score (0-10) | Customer loyalty |
| Slider | Visual slider input | Ranges, preferences |
| Matrix | Grid of options | Multiple ratings |
| Ranking | Drag to rank items | Priority ordering |
| Signature | Electronic signature | Agreements, consent |
| Location | Geographic location | Address, coordinates |
| Hidden | Hidden field | Tracking, metadata |
| Calculated | Auto-calculated field | Totals, averages |

## 🔒 Security Features

- Input sanitization
- XSS prevention
- SQL injection protection
- Spam detection
- Rate limiting support
- CAPTCHA integration ready
- Data encryption ready
- Access control

## 🌍 Internationalization

The module is designed for easy internationalization:
- All UI strings are extractable
- Date/time formatting support
- Multi-language form support (coming soon)

## 📈 Performance

- Optimized for large forms (100+ fields)
- Efficient response storage
- Fast analytics calculations
- Pagination for large datasets
- Lazy loading support

## 🔮 Future Enhancements

- [ ] Payment integration (Stripe, PayPal)
- [ ] Advanced scoring for quizzes
- [ ] Workflow automation
- [ ] Advanced reporting
- [ ] Mobile app
- [ ] API endpoints
- [ ] Webhook support
- [ ] CRM integrations
- [ ] A/B testing
- [ ] Multi-language support

## 📝 API Reference

### FormBuilder

```python
builder = FormBuilder()

# Create form
form = builder.create_form(title: str) -> Form

# Get form
form = builder.get_form(form_id: str) -> Optional[Form]

# List forms
forms = builder.list_forms(status: Optional[str] = None) -> List[Form]

# Delete form
success = builder.delete_form(form_id: str) -> bool

# Duplicate form
new_form = builder.duplicate_form(form_id: str) -> Optional[Form]
```

### Form

```python
# Add field
form.add_field(field: Field, position: Optional[int] = None)

# Remove field
success = form.remove_field(field_id: str) -> bool

# Move field
success = form.move_field(field_id: str, new_position: int) -> bool

# Publish form
share_link = form.publish() -> str

# Validate submission
is_valid, errors = form.validate_submission(data: Dict) -> Tuple[bool, Dict]
```

### ResponseManager

```python
manager = ResponseManager()

# Submit response
response_id = manager.submit_response(response: FormResponse) -> str

# Get responses
responses = manager.get_form_responses(form_id: str) -> List[FormResponse]

# Filter responses
filtered = manager.filter_responses(form_id: str, filters: Dict) -> List[FormResponse]

# Search responses
results = manager.search_responses(form_id: str, search_term: str) -> List[FormResponse]
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Write tests for new features
2. Follow PEP 8 style guide
3. Add type hints
4. Update documentation
5. Create descriptive commit messages

## 📄 License

Part of the NEXUS platform. All rights reserved.

## 💬 Support

For questions or issues:
- Create an issue in the NEXUS repository
- Contact the NEXUS development team
- Check the documentation

## 🎉 Credits

Developed as part of NEXUS Session 26: Forms & Surveys Module

Built with ❤️ using:
- Python 3.8+
- Streamlit
- Plotly
- Pandas
- And other amazing open-source libraries

---

**Ready to create amazing forms?** Start with `streamlit run modules/forms/streamlit_ui.py` 🚀

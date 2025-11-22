# NEXUS Testing & QA Module

A comprehensive, production-ready testing and quality assurance framework for the NEXUS platform with 24+ advanced testing capabilities.

## 🌟 Features

### Core Testing Capabilities

1. **Unit Testing** - Generate and run pytest unit tests with 80%+ coverage
2. **Integration Testing** - Test API endpoints, database operations, module interactions
3. **End-to-End Testing** - Browser automation with Selenium/Playwright
4. **API Testing** - Automated endpoint testing, request/response validation
5. **Load Testing** - Performance testing, stress testing, capacity planning
6. **Security Testing** - Vulnerability scanning, penetration testing, OWASP checks
7. **Code Coverage** - Track coverage metrics, generate detailed reports
8. **Test Data Generation** - Generate realistic mock data, fixtures, factories

### Advanced Features

9. **CI/CD Integration** - GitHub Actions, Jenkins, CircleCI integration
10. **Visual Regression** - Screenshot comparison, pixel-perfect testing
11. **Accessibility Testing** - WCAG compliance, ARIA validation
12. **Mutation Testing** - Code mutation to verify test quality
13. **Contract Testing** - API contract verification, schema validation
14. **AI Test Generation** - Claude/GPT-4 powered test creation
15. **Test Reporting** - HTML, JUnit, Allure reports with metrics
16. **Bug Tracking** - Detect, log, and track bugs automatically

### Infrastructure

17. **Parallel Execution** - Run tests in parallel for faster execution
18. **Test Flakiness Detection** - Identify and report flaky tests
19. **Custom Assertions** - Rich assertion library for complex validations
20. **Mock Management** - Comprehensive mocking for dependencies
21. **Test Analytics** - Historical trends, failure patterns, insights
22. **WebSocket Testing** - Real-time feature testing
23. **Database Testing** - Schema validation, migration testing
24. **Cross-browser Testing** - Multi-browser compatibility testing

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install browser drivers for E2E testing
playwright install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

## 🚀 Quick Start

### Running Unit Tests

```python
from modules.testing_qa.test_framework import TestRunner, TestSuiteManager

# Create test suite manager
suite_manager = TestSuiteManager()

# Discover tests
tests = suite_manager.discover_tests(pattern="test_*.py")

# Create suite
suite = suite_manager.create_suite(
    name="unit_tests",
    test_files=[t["file_path"] for t in tests],
    test_type="unit"
)

# Run tests
runner = TestRunner()
results = await runner.run_test_suite("unit_tests", suite_manager)
```

### Generating AI Tests

```python
from modules.testing_qa.ai_testing import AITestGenerator

# Initialize AI test generator
generator = AITestGenerator(api_key="your-api-key")

# Generate comprehensive tests
results = await generator.generate_comprehensive_tests(
    source_file="modules/auth/authentication.py",
    output_file="tests/test_authentication.py",
    test_types=["unit", "integration"]
)
```

### Running API Tests

```python
from modules.testing_qa.api_testing import EndpointTester

# Initialize endpoint tester
tester = EndpointTester(base_url="http://localhost:8000")

# Test endpoint
result = await tester.test_get(
    "/api/v1/users",
    expected_status=200,
    max_response_time_ms=500
)
```

### Load Testing

```python
from modules.testing_qa.load_testing import LoadTester

# Initialize load tester
tester = LoadTester(base_url="http://localhost:8000")

# Run load test
results = await tester.run_load_test(
    endpoint="/api/v1/users",
    concurrent_users=100,
    total_requests=10000
)
```

### Security Scanning

```python
from modules.testing_qa.security_testing import SecurityScanner

# Initialize scanner
scanner = SecurityScanner(base_url="http://localhost:8000")

# Scan code for vulnerabilities
with open("my_code.py", "r") as f:
    code = f.read()

results = await scanner.scan_code(code, "my_code.py")
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/testing_qa

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI Integration
ANTHROPIC_API_KEY=your-api-key

# Test Settings
TEST_TIMEOUT=300
MAX_RETRIES=3
PARALLEL_WORKERS=4
```

## 📊 Dashboard

Start the Streamlit dashboard:

```bash
streamlit run modules/testing_qa/ui.py
```

Access at: http://localhost:8501

## 🌐 API Endpoints

Start the FastAPI server:

```bash
uvicorn modules.testing_qa.api:router --reload
```

API Documentation: http://localhost:8000/docs

### Key Endpoints

- `POST /api/v1/testing/suites` - Create test suite
- `GET /api/v1/testing/suites` - List test suites
- `POST /api/v1/testing/execute` - Execute tests
- `GET /api/v1/testing/analytics` - Get test analytics
- `POST /api/v1/testing/ai/generate-tests` - Generate AI tests
- `POST /api/v1/testing/load-test` - Run load test
- `POST /api/v1/testing/security/scan` - Run security scan

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest --cov --junitxml=junit.xml
```

Generate workflow:

```python
from modules.testing_qa.ci_cd import CIIntegration

ci = CIIntegration()
ci.setup_ci("github", python_versions=["3.9", "3.10", "3.11"])
```

## 📈 Test Reporting

### Generate Reports

```python
from modules.testing_qa.reporting import TestReporter

reporter = TestReporter()

# Generate multiple formats
reports = reporter.generate_reports(
    test_results=results,
    formats=["html", "junit", "allure"],
    output_dir="test-reports"
)
```

### Report Formats

- **HTML** - Human-readable reports with charts
- **JUnit XML** - CI/CD compatible format
- **Allure** - Advanced reporting with history
- **JSON** - Machine-readable format

## 🧪 Test Data Generation

```python
from modules.testing_qa.test_data import TestDataGenerator

# Initialize generator
generator = TestDataGenerator(seed=42)

# Generate test data
users = generator.generate_batch("person", count=100)
products = generator.generate_batch("product", count=50)

# Generate edge cases
edge_cases = generator.generate_edge_cases("string")

# Generate security payloads
sql_injections = generator.generate_sql_injection_payloads()
xss_payloads = generator.generate_xss_payloads()
```

## 🔐 Security Testing

### Code Scanning

```python
from modules.testing_qa.security_testing import SecurityScanner

scanner = SecurityScanner()

# Scan code file
results = await scanner.scan_code(code, "auth.py")

# Generate report
report = scanner.generate_security_report(results)
```

### Vulnerability Detection

- SQL Injection
- Cross-Site Scripting (XSS)
- Hardcoded Secrets
- Weak Cryptography
- OWASP Top 10

## 📱 Accessibility Testing

```python
from modules.testing_qa.accessibility import AccessibilityTester

tester = AccessibilityTester(wcag_level="AA")

# Test page
results = await tester.test_page(page_content)

# Generate report
report = tester.generate_report(results)
```

## 🎯 Code Coverage

```python
from modules.testing_qa.coverage import CoverageAnalyzer

analyzer = CoverageAnalyzer()

# Analyze coverage
analysis = analyzer.analyze(generate_reports=True)

# Get coverage percentage
coverage_pct = analyzer.get_coverage_percentage()

# Get uncovered lines
uncovered = analyzer.get_uncovered_lines("my_module.py")
```

## 🔄 Async Task Execution

```python
from modules.testing_qa.tasks import run_test_suite_task

# Queue test execution
task = run_test_suite_task.delay(suite_id=1)

# Check status
result = task.get()
```

## 📚 Database Models

- **TestSuite** - Test suite configuration
- **TestCase** - Individual test cases
- **TestRun** - Test execution sessions
- **TestExecution** - Individual test executions
- **BugReport** - Bug tracking
- **CoverageReport** - Coverage data
- **TestMetrics** - Analytics and trends
- **FlakynessRecord** - Flaky test tracking

## 🛠️ Advanced Usage

### Visual Regression Testing

```python
from modules.testing_qa.visual_testing import VisualRegression

tester = VisualRegression(baseline_dir="baselines")

# Test screenshot
result = tester.test_screenshot(
    "screenshot.png",
    "homepage",
    update_baseline=False
)
```

### Mutation Testing

```python
from modules.testing_qa.mutation_testing import MutationTester

tester = MutationTester()

# Run mutation tests
results = await tester.run_mutation_test(
    "source.py",
    "test_source.py"
)
```

### Contract Testing

```python
from modules.testing_qa.contract_testing import ContractValidator

validator = ContractValidator()

# Load contract
contract = validator.load_contract("contract.json")

# Validate interaction
result = validator.validate_interaction(interaction, contract)
```

## 📊 Analytics & Metrics

```python
from modules.testing_qa.reporting import TestReporter

reporter = TestReporter()

# Generate summary
summary = reporter.generate_summary(test_results)

print(f"Pass Rate: {summary['pass_rate']}%")
print(f"Average Time: {summary['average_execution_time_ms']}ms")
```

## 🤝 Integration with NEXUS Modules

The Testing & QA module integrates with:

- **Auth Module** - Authentication testing
- **Database Module** - Database testing
- **AI Orchestrator** - AI-powered testing
- **Notifications** - Test result alerts
- **Analytics** - Test metrics and trends

## 📝 Best Practices

1. **Write tests first** - Follow TDD principles
2. **Aim for 80%+ coverage** - Use coverage tools
3. **Use descriptive test names** - Make tests self-documenting
4. **Mock external dependencies** - Isolate unit tests
5. **Run tests in CI/CD** - Automate testing
6. **Monitor test metrics** - Track trends
7. **Fix flaky tests** - Maintain test stability
8. **Use AI generation** - Accelerate test creation

## 🐛 Troubleshooting

### Tests Timing Out

```python
# Increase timeout
runner = TestRunner(timeout_seconds=600)
```

### Flaky Tests

```python
# Enable retry logic
runner = TestRunner(max_retries=3)
```

### Database Connection Issues

```python
# Check DATABASE_URL in .env
# Verify database is running
```

## 📄 License

Part of the NEXUS Platform - All Rights Reserved

## 🤝 Contributing

See NEXUS Platform contribution guidelines.

## 📞 Support

For support, contact the NEXUS Platform team.

---

Built with ❤️ for the NEXUS Platform

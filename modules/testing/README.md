# NEXUS Testing & QA Module

Comprehensive automated testing and quality assurance module with test management, CI/CD integration, multiple test types, and detailed reporting.

## Features

### Test Types
- **Unit Tests**: Fast, isolated component tests with pytest
- **Integration Tests**: API and database integration testing
- **E2E Tests**: Browser-based end-to-end tests with Selenium
- **Performance Tests**: Load and stress testing with metrics
- **Security Tests**: Vulnerability scanning and OWASP Top 10 checks
- **Regression Tests**: Automated regression test suites

### Core Capabilities
- Test suite and test case management
- Automated test execution
- Real-time test monitoring
- Coverage reporting (line, branch, function)
- Defect tracking and management
- CI/CD pipeline integration (GitHub Actions)
- Performance metrics and benchmarking
- Security vulnerability scanning
- Detailed test reports and analytics

### Technical Features
- FastAPI REST API
- PostgreSQL database for test data
- Redis for caching and queuing
- Pytest test framework
- Selenium WebDriver for E2E tests
- Comprehensive Streamlit UI
- GitHub Actions workflows
- HTML and JSON test reports

## Architecture

```
modules/testing/
├── api/                      # FastAPI application
│   └── main.py              # API endpoints
├── models/                  # Data models
│   ├── database.py          # SQLAlchemy models
│   └── schemas.py           # Pydantic schemas
├── services/                # Business logic
│   ├── test_executor.py     # Test execution engine
│   ├── selenium_runner.py   # E2E test runner
│   ├── performance_tester.py # Performance testing
│   └── security_scanner.py  # Security scanning
├── ui/                      # User interface
│   └── streamlit_app.py     # Streamlit dashboard
├── config/                  # Configuration
│   └── settings.py          # Settings management
└── tests/                   # Test suite
    ├── unit/
    ├── integration/
    ├── e2e/
    └── performance/
```

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- Redis 7+
- Chrome/Chromium (for E2E tests)

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Install ChromeDriver** (for E2E tests):
```bash
# Ubuntu/Debian
apt-get install chromium-driver

# macOS
brew install chromedriver

# Or use webdriver-manager (automatic)
pip install webdriver-manager
```

4. **Initialize database**:
```bash
# Database tables are created automatically on first run
python -c "from modules.testing.api.main import app"
```

## Usage

### Starting the API Server

```bash
# Development
uvicorn modules.testing.api.main:app --reload --port 8002

# Production
uvicorn modules.testing.api.main:app --host 0.0.0.0 --port 8002 --workers 4
```

### Starting the Streamlit UI

```bash
streamlit run modules/testing/ui/streamlit_app.py --server.port 8502
```

### Using Docker

```bash
# Build and start all services
docker-compose up -d

# Access services:
# - API: http://localhost:8002
# - UI: http://localhost:8502
# - API Docs: http://localhost:8002/docs
```

## API Endpoints

### Test Suites

```bash
# Create test suite
POST /suites
Content-Type: application/json

{
  "name": "API Test Suite",
  "description": "Integration tests for API",
  "test_type": "integration",
  "environment": "staging",
  "created_by": 1
}

# Get test suites
GET /suites?test_type=integration

# Get specific suite
GET /suites/{suite_id}
```

### Test Cases

```bash
# Create test case
POST /cases
Content-Type: application/json

{
  "suite_id": 1,
  "name": "Test user authentication",
  "description": "Verify user can login with valid credentials",
  "test_type": "integration",
  "priority": "high",
  "file_path": "tests/test_auth.py",
  "function_name": "test_login_success",
  "created_by": 1
}

# Get test cases
GET /cases?suite_id=1&status=passed

# Get specific case
GET /cases/{case_id}
```

### Test Runs

```bash
# Execute test run
POST /runs
Content-Type: application/json

{
  "suite_id": 1,
  "name": "Nightly Regression",
  "run_type": "automated",
  "environment": "staging",
  "triggered_by": 1
}

# Get test runs
GET /runs?suite_id=1&status=completed

# Get run details
GET /runs/{run_id}

# Get run executions
GET /runs/{run_id}/executions
```

### Defects

```bash
# Create defect
POST /defects
Content-Type: application/json

{
  "title": "Login button not working",
  "description": "Login button does not respond to clicks",
  "severity": "high",
  "priority": "critical",
  "test_case_id": 5,
  "environment": "production",
  "browser": "Chrome 120",
  "reported_by": 1
}

# Get defects
GET /defects?severity=high&status=open

# Update defect status
PATCH /defects/{defect_id}/status?status=resolved
```

### Analytics

```bash
# Get analytics
GET /analytics?days=30
```

## Test Execution

### Running Unit Tests

```bash
# Run all unit tests
pytest modules/testing/tests/unit -v

# Run specific test file
pytest modules/testing/tests/unit/test_api.py -v

# Run with coverage
pytest modules/testing/tests/unit --cov=modules.testing --cov-report=html
```

### Running Integration Tests

```bash
# Run integration tests
pytest modules/testing/tests/integration -v

# With markers
pytest -m integration -v
```

### Running E2E Tests

```bash
# Run E2E tests
pytest modules/testing/tests/e2e -v

# Headless mode
pytest modules/testing/tests/e2e -v --headless

# With screenshots on failure
pytest modules/testing/tests/e2e -v --screenshots
```

### Running Performance Tests

```bash
# Run performance tests
pytest modules/testing/tests/performance --benchmark-only

# With detailed metrics
pytest modules/testing/tests/performance --benchmark-verbose
```

## CI/CD Integration

### GitHub Actions

The module includes comprehensive GitHub Actions workflows:

**Workflow: `ci-testing.yml`**
- Unit tests across Python 3.9, 3.10, 3.11
- Integration tests with PostgreSQL & Redis
- E2E tests with Chrome
- Security scanning (Bandit, Safety)
- Performance tests
- Code quality checks (pylint, flake8, black)
- Coverage reporting
- Automated deployment

### Running CI Locally

```bash
# Run all tests like CI
pytest modules/testing/tests -v --cov=modules.testing --cov-report=html

# Run security scan
bandit -r modules/testing

# Check code quality
pylint modules/testing
flake8 modules/testing
black --check modules/testing
```

## Configuration

### Test Execution Settings

Edit `modules/testing/config/settings.py`:

```python
# Selenium Configuration
SELENIUM_HUB_URL = "http://localhost:4444/wd/hub"
WEBDRIVER_HEADLESS = True
WEBDRIVER_TIMEOUT = 30

# Pytest Configuration
PYTEST_ARGS = ["-v", "--tb=short"]
PYTEST_MARKERS = ["unit", "integration", "e2e", "slow"]

# Coverage
COVERAGE_MIN_THRESHOLD = 80.0

# Performance Testing
LOAD_TEST_USERS = 10
LOAD_TEST_DURATION = 60
PERFORMANCE_THRESHOLD_MS = 1000
```

## Examples

### Creating and Running Tests via API

```python
import requests

API_BASE = "http://localhost:8002"

# Create test suite
suite_response = requests.post(f"{API_BASE}/suites", json={
    "name": "User Management Tests",
    "test_type": "integration",
    "created_by": 1
})
suite = suite_response.json()

# Create test case
case_response = requests.post(f"{API_BASE}/cases", json={
    "suite_id": suite['id'],
    "name": "Test user creation",
    "test_type": "integration",
    "code": """
def test_create_user():
    response = requests.post('/api/users', json={'name': 'John'})
    assert response.status_code == 201
    """,
    "created_by": 1
})

# Execute test run
run_response = requests.post(f"{API_BASE}/runs", json={
    "suite_id": suite['id'],
    "name": "Test Run 1",
    "triggered_by": 1
})
run = run_response.json()

# Check results
results = requests.get(f"{API_BASE}/runs/{run['id']}")
print(results.json())
```

### Writing Test Cases

**Unit Test Example**:
```python
# tests/unit/test_calculator.py
import pytest

def test_addition():
    assert 1 + 1 == 2

def test_division():
    assert 10 / 2 == 5

def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0
```

**Integration Test Example**:
```python
# tests/integration/test_api.py
import pytest
import requests

@pytest.fixture
def api_client():
    return requests.Session()

def test_get_users(api_client):
    response = api_client.get('http://localhost:8000/api/users')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**E2E Test Example**:
```python
# tests/e2e/test_login.py
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_user_login():
    driver = webdriver.Chrome()
    driver.get('http://localhost:3000/login')

    driver.find_element(By.ID, 'username').send_keys('testuser')
    driver.find_element(By.ID, 'password').send_keys('password123')
    driver.find_element(By.ID, 'login-btn').click()

    assert 'Dashboard' in driver.title
    driver.quit()
```

## Test Reports

### HTML Reports

```bash
# Generate HTML report
pytest --html=reports/test-report.html --self-contained-html
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=modules.testing --cov-report=html

# View report
open htmlcov/index.html
```

### JSON Reports

```bash
# Generate JSON report
pytest --json-report --json-report-file=reports/test-report.json
```

## Performance Testing

### Load Testing Example

```python
from modules.testing.services.performance_tester import PerformanceTester

tester = PerformanceTester()

config = {
    "url": "http://localhost:8000/api/health",
    "concurrent_users": 50,
    "duration_seconds": 60,
    "method": "GET"
}

results = tester.run_load_test(config)
print(f"Throughput: {results['metrics']['throughput_rps']} req/s")
print(f"Avg Response Time: {results['metrics']['avg_response_time_ms']} ms")
```

## Security Testing

### Running Security Scans

```python
from modules.testing.services.security_scanner import SecurityScanner

scanner = SecurityScanner()

config = {
    "url": "https://example.com",
    "scan_type": "owasp"
}

results = scanner.run_scan({"test_data": config})
print(f"Vulnerabilities found: {results['summary']['total']}")
```

## Best Practices

1. **Test Organization**: Organize tests by type (unit, integration, e2e)
2. **Test Naming**: Use descriptive names (test_user_can_login_with_valid_credentials)
3. **Test Isolation**: Each test should be independent
4. **Fixtures**: Use pytest fixtures for setup/teardown
5. **Assertions**: Use meaningful assertion messages
6. **Coverage**: Aim for >80% code coverage
7. **Performance**: Keep unit tests fast (<100ms)
8. **CI Integration**: Run tests automatically on every commit

## Troubleshooting

### Common Issues

1. **Selenium WebDriver errors**:
   ```bash
   # Install/update ChromeDriver
   pip install webdriver-manager
   ```

2. **Database connection errors**:
   ```bash
   # Check PostgreSQL is running
   systemctl status postgresql

   # Verify connection
   psql -h localhost -U nexus_user -d nexus_db
   ```

3. **Test timeouts**:
   ```python
   # Increase timeout in pytest.ini
   [pytest]
   timeout = 300
   ```

## Monitoring

### Test Execution Monitoring

- Real-time test status in Streamlit UI
- Test run history and trends
- Defect tracking dashboard
- Performance metrics visualization

### Metrics

- Test pass rate
- Average execution time
- Coverage percentage
- Defect density
- Flaky test detection

## Contributing

1. Write tests for new features
2. Ensure all tests pass
3. Maintain >80% coverage
4. Follow coding standards
5. Document test cases

## License

Part of the NEXUS platform - See main README for license information.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation
- Contact the QA team

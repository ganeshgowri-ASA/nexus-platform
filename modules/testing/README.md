# NEXUS Testing & QA Module

<<<<<<< HEAD
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
=======
## Overview

The Testing & QA module provides comprehensive automated testing capabilities including unit tests, integration tests, E2E tests, performance testing, security testing, test management, defect tracking, and CI/CD integration.

## Features

- **Test Execution**: Run unit, integration, and E2E tests
- **Test Management**: Create and manage test cases and test suites
- **Test Reporting**: Detailed reports with coverage analysis
- **Defect Tracking**: Track bugs and issues
- **CI/CD Integration**: GitHub Actions workflows
- **Performance Testing**: Load and performance metrics
- **Security Testing**: Automated security scans
- **RESTful API**: FastAPI-based API
- **Web UI**: Streamlit interface for test management
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

## Architecture

```
modules/testing/
<<<<<<< HEAD
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
=======
├── api/                    # FastAPI application
│   └── main.py            # API endpoints
├── models/                 # Database models and schemas
│   ├── database.py        # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   └── db_connection.py   # Database connection
├── services/              # Business logic
│   ├── test_execution_service.py
│   └── redis_cache.py
├── runners/               # Test runners
│   ├── pytest_runner.py
│   └── selenium_runner.py
├── ui/                    # Streamlit UI
│   └── streamlit_app.py
└── pipelines/             # CI/CD configurations
    └── github_actions/
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
```

## Installation

### Prerequisites
<<<<<<< HEAD
- Python 3.9+
- PostgreSQL 14+
- Redis 7+
- Chrome/Chromium (for E2E tests)
=======

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Chrome/Firefox (for E2E tests)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

### Setup

1. **Install dependencies**:
<<<<<<< HEAD
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
=======
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

3. **Initialize database**:
   ```bash
   python -c "from modules.testing.models.db_connection import init_db; init_db()"
   ```

4. **Start services**:
   ```bash
   # Redis
   redis-server

   # API server
   uvicorn modules.testing.api.main:app --reload --port 8001

   # UI
   streamlit run modules/testing/ui/streamlit_app.py --server.port 8502
   ```

## Docker Deployment

```bash
docker-compose up -d
```

Services:
- Testing API (port 8001)
- Streamlit UI (port 8502)
- PostgreSQL
- Redis

## Quick Start

### Creating Test Cases

```python
import requests

# Create a unit test case
data = {
    "name": "Test user authentication",
    "description": "Verify user can login with valid credentials",
    "test_type": "unit",
    "priority": "high",
    "test_file": "tests/test_auth.py",
    "test_function": "test_login_success",
    "is_automated": True
}

response = requests.post('http://localhost:8001/test-cases', json=data)
test_case = response.json()
print(f"Created test case: {test_case['id']}")
```

### Creating Test Suites

```python
# Create a test suite
data = {
    "name": "Authentication Test Suite",
    "description": "All authentication-related tests",
    "test_case_ids": [1, 2, 3, 4],
    "environment": "staging"
}

response = requests.post('http://localhost:8001/test-suites', json=data)
suite = response.json()
```

### Running Tests

```python
# Create and execute test run
data = {
    "test_suite_id": 1,
    "name": "Nightly Test Run",
    "environment": "staging",
    "branch": "develop",
    "triggered_by": "CI/CD"
}

response = requests.post('http://localhost:8001/test-runs', json=data)
test_run = response.json()

# Check status
response = requests.get(f'http://localhost:8001/test-runs/{test_run["id"]}')
results = response.json()

print(f"Status: {results['status']}")
print(f"Passed: {results['passed_tests']}/{results['total_tests']}")
```

### Creating Defects

```python
# Report a defect
data = {
    "title": "Login button not working",
    "description": "The login button doesn't respond to clicks",
    "severity": "high",
    "priority": "critical",
    "steps_to_reproduce": "1. Go to login page\n2. Click login button\n3. Nothing happens",
    "expected_behavior": "User should be redirected to dashboard",
    "actual_behavior": "Button click has no effect",
    "environment": "production",
    "browser": "Chrome 120"
}

response = requests.post('http://localhost:8001/defects', json=data)
defect = response.json()
```

## Test Types

### Unit Tests
- Fast, isolated tests
- Test individual functions/methods
- Use pytest framework

### Integration Tests
- Test component interactions
- Database, API, service integration
- Use pytest with fixtures

### E2E Tests
- Full user workflow testing
- Browser automation with Selenium
- Test complete user journeys

### Performance Tests
- Load testing
- Response time metrics
- Resource usage monitoring

### Security Tests
- Vulnerability scanning
- Dependency checks
- Code security analysis

## Test Execution

### Using Pytest Runner

```python
from modules.testing.runners.pytest_runner import PytestRunner

runner = PytestRunner()

# Run all tests
results = runner.run_tests(
    test_paths=['tests/'],
    parallel=True,
    max_workers=4,
    coverage_enabled=True
)

print(f"Total: {results['test_results']['total']}")
print(f"Passed: {results['test_results']['passed']}")
print(f"Coverage: {results['coverage']['line_coverage']}%")
```

### Using Selenium Runner

```python
from modules.testing.runners.selenium_runner import SeleniumRunner

runner = SeleniumRunner(browser='chrome', headless=True)

# Define test steps
steps = [
    {"action": "navigate", "target": "https://example.com"},
    {"action": "click", "target": "login-button", "by": "id"},
    {"action": "type", "target": "username", "value": "testuser", "by": "id"},
    {"action": "type", "target": "password", "value": "password123", "by": "id"},
    {"action": "click", "target": "submit", "by": "id"},
    {"action": "assert_element", "target": "dashboard", "by": "id"}
]

results = runner.run_test_scenario(
    test_name="Login Flow",
    steps=steps,
    base_url="https://example.com"
)

print(f"Status: {results['status']}")
```

## Database Schema

### TestCase
- Test definition and metadata
- Test type, priority, automation status
- Pre/post conditions, expected results

### TestSuite
- Collection of test cases
- Environment configuration
- Parallel execution settings

### TestRun
- Test execution instance
- Results summary (passed/failed/skipped)
- Coverage and duration metrics

### TestExecution
- Individual test execution
- Status, duration, error details
- Logs and screenshots

### Defect
- Bug/issue tracking
- Severity, priority, status
- Steps to reproduce, resolution

### CoverageReport
- Code coverage metrics
- Line, branch, function coverage
- File-level coverage details

### PerformanceMetric
- Performance test results
- Response times, throughput
- Resource usage metrics

## API Endpoints

### Test Cases
- `POST /test-cases` - Create test case
- `GET /test-cases` - List test cases
- `GET /test-cases/{id}` - Get test case
- `PUT /test-cases/{id}` - Update test case
- `DELETE /test-cases/{id}` - Delete test case

### Test Suites
- `POST /test-suites` - Create test suite
- `GET /test-suites` - List test suites
- `GET /test-suites/{id}` - Get test suite

### Test Runs
- `POST /test-runs` - Create and execute test run
- `POST /test-runs/{id}/execute` - Execute existing run
- `GET /test-runs` - List test runs
- `GET /test-runs/{id}` - Get test run
- `GET /test-runs/{id}/executions` - Get test executions

### Defects
- `POST /defects` - Create defect
- `GET /defects` - List defects
- `GET /defects/{id}` - Get defect
- `PATCH /defects/{id}` - Update defect

### Analytics
- `GET /analytics` - Get test analytics
- `GET /coverage/{test_run_id}` - Get coverage report
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

## CI/CD Integration

### GitHub Actions

<<<<<<< HEAD
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
=======
The module includes a comprehensive CI/CD pipeline (`.github/workflows/testing-ci.yml`):

**Features:**
- Automated test execution on push/PR
- Code quality checks (Black, isort, Flake8, mypy)
- Security scanning (Bandit, Safety)
- Coverage reporting
- Documentation building
- Daily scheduled runs

**Workflow Jobs:**
1. **test**: Run all tests with coverage
2. **lint**: Code quality checks
3. **security**: Security scanning
4. **build-docs**: Documentation generation
5. **performance**: Performance tests (scheduled)

**Usage:**
```yaml
# Triggered automatically on:
- Push to main/develop
- Pull requests
- Daily at 2 AM (scheduled)
```

### Integration with CI/CD Tools

```bash
# Jenkins
pipeline {
    stage('Test') {
        steps {
            sh 'pytest modules/testing/tests/'
        }
    }
}

# GitLab CI
test:
  script:
    - pytest modules/testing/tests/ --cov=modules/testing
```

## Redis Caching

The module uses Redis for caching test results and analytics:

```python
from modules.testing.services.redis_cache import cache

# Cache test results
cache.cache_test_results(test_run_id=1, results=data, expire=3600)

# Get cached results
results = cache.get_cached_test_results(test_run_id=1)

# Cache analytics
cache.cache_test_analytics(analytics_data, expire=300)

# Clear cache
cache.clear_cache(pattern="test_run:*")
```

## Test Reporting

### Coverage Reports

```python
# Generate coverage report
pytest --cov=modules/testing --cov-report=html --cov-report=xml

# View HTML report
open htmlcov/index.html
```

### Test Reports

- HTML reports with detailed results
- JSON reports for programmatic access
- Coverage reports (line, branch, function)
- Performance metrics
- Screenshots for E2E test failures

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nexus_testing

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Testing
TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/nexus_testing_test

# Selenium
SELENIUM_BROWSER=chrome
SELENIUM_HEADLESS=true
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
```

## Best Practices

<<<<<<< HEAD
1. **Test Organization**: Organize tests by type (unit, integration, e2e)
2. **Test Naming**: Use descriptive names (test_user_can_login_with_valid_credentials)
3. **Test Isolation**: Each test should be independent
4. **Fixtures**: Use pytest fixtures for setup/teardown
5. **Assertions**: Use meaningful assertion messages
6. **Coverage**: Aim for >80% code coverage
7. **Performance**: Keep unit tests fast (<100ms)
8. **CI Integration**: Run tests automatically on every commit
=======
1. **Test Organization**
   - Group related tests in suites
   - Use descriptive test names
   - Keep tests independent

2. **Test Data**
   - Use fixtures for test data
   - Clean up after tests
   - Use separate test database

3. **Coverage**
   - Aim for >80% code coverage
   - Focus on critical paths
   - Test edge cases

4. **Performance**
   - Run tests in parallel
   - Use caching for repeated operations
   - Optimize slow tests

5. **CI/CD**
   - Run tests on every commit
   - Block merges on test failures
   - Monitor test trends

## Monitoring

### Test Analytics Dashboard

Access analytics at `http://localhost:8502` (Streamlit UI):

- Test execution trends
- Pass/fail rates
- Test duration metrics
- Defect statistics
- Coverage trends

### API Monitoring

```python
# Get analytics
response = requests.get('http://localhost:8001/analytics')
analytics = response.json()

print(f"Total tests: {analytics['total_test_cases']}")
print(f"Pass rate: {analytics['test_pass_rate']}%")
print(f"Active defects: {analytics['active_defects']}")
```
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

## Troubleshooting

### Common Issues

<<<<<<< HEAD
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
=======
1. **Tests Not Running**
   ```bash
   # Check test discovery
   pytest --collect-only
   ```

2. **Database Connection**
   ```bash
   # Verify connection
   psql -U postgres -d nexus_testing
   ```

3. **Selenium Issues**
   ```bash
   # Install ChromeDriver
   pip install webdriver-manager
   ```

4. **Redis Connection**
   ```bash
   # Test Redis
   redis-cli ping
   ```

## Testing the Module Itself

```bash
# Run module tests
pytest modules/testing/tests/ -v

# With coverage
pytest modules/testing/tests/ --cov=modules/testing --cov-report=html

# Run specific test type
pytest modules/testing/tests/ -m "unit"
pytest modules/testing/tests/ -m "integration"
```

## Performance Optimization

1. **Parallel Execution**: Run tests in parallel with pytest-xdist
2. **Redis Caching**: Cache test results and analytics
3. **Connection Pooling**: Database connection optimization
4. **Selective Testing**: Run only affected tests

## Security Considerations

1. **Test Data**: Use anonymized data in tests
2. **Credentials**: Never commit credentials
3. **Access Control**: Implement API authentication
4. **Audit Logs**: Track test executions and changes
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

## Contributing

1. Write tests for new features
<<<<<<< HEAD
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
=======
2. Follow code style guidelines
3. Update documentation
4. Submit pull request

## License

MIT License

## Support

- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [Full docs](https://docs.nexus-platform.com)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

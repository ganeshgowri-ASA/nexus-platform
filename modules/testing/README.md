# NEXUS Testing & QA Module

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

## Architecture

```
modules/testing/
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
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Chrome/Firefox (for E2E tests)

### Setup

1. **Install dependencies**:
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

## CI/CD Integration

### GitHub Actions

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
```

## Best Practices

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

## Troubleshooting

### Common Issues

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

## Contributing

1. Write tests for new features
2. Follow code style guidelines
3. Update documentation
4. Submit pull request

## License

MIT License

## Support

- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [Full docs](https://docs.nexus-platform.com)

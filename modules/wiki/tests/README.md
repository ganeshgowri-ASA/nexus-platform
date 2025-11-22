# NEXUS Wiki System - Test Suite

Comprehensive unit tests for the NEXUS Wiki System.

## Overview

This test suite provides extensive coverage for all major components of the wiki system:

- **Page Management** (`test_pages.py`) - CRUD operations, hierarchies, slug generation
- **Version Control** (`test_versioning.py`) - History tracking, diffs, rollback
- **Search** (`test_search.py`) - Full-text search, filters, suggestions
- **Permissions** (`test_permissions.py`) - Access control, inheritance, roles
- **Categories & Tags** (`test_categories.py`) - Hierarchies, auto-categorization, tag management

## Test Coverage

- **conftest.py**: Pytest fixtures and test configuration (300+ lines)
- **test_pages.py**: 45+ tests for page management
- **test_versioning.py**: 35+ tests for versioning and history
- **test_search.py**: 55+ tests for search functionality
- **test_permissions.py**: 40+ tests for access control
- **test_categories.py**: 45+ tests for categories and tags

**Total: 220+ comprehensive unit tests**

## Running Tests

### Run All Tests

```bash
cd /home/user/nexus-platform/modules/wiki
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_pages.py -v
pytest tests/test_versioning.py -v
pytest tests/test_search.py -v
pytest tests/test_permissions.py -v
pytest tests/test_categories.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_pages.py::TestPageCreation -v
pytest tests/test_search.py::TestSearchFilters -v
```

### Run Specific Test

```bash
pytest tests/test_pages.py::TestPageCreation::test_create_basic_page -v
```

### Run with Coverage

```bash
pytest tests/ --cov=modules.wiki --cov-report=html --cov-report=term
```

### Run Only Fast Tests (exclude slow tests)

```bash
pytest tests/ -v -m "not slow"
```

### Run Only Permission Tests

```bash
pytest tests/ -v -m permissions
```

## Test Structure

### conftest.py - Fixtures

Provides reusable fixtures for all tests:

**Database Fixtures:**
- `engine` - SQLAlchemy engine for testing (in-memory SQLite)
- `db_session` - Transaction-isolated database session

**User Fixtures:**
- `mock_user` - Standard test user
- `mock_admin_user` - Admin user for testing
- `mock_viewer_user` - Read-only user

**Data Fixtures:**
- `sample_category` - Single test category
- `sample_categories` - Multiple categories with hierarchy
- `sample_tags` - Pre-created tags
- `sample_page` - Single test page
- `sample_pages` - Multiple test pages
- `sample_page_with_history` - Page with version history
- `sample_permissions` - Pre-configured permissions

**Factory Fixtures:**
- `page_factory` - Function to create custom pages
- `category_factory` - Function to create custom categories
- `tag_factory` - Function to create custom tags

### Test Organization

Each test file follows this structure:

1. **Class-based organization** - Tests grouped by functionality
2. **Descriptive test names** - Clear purpose in test name
3. **Comprehensive docstrings** - Explains what each test does
4. **Happy path and error cases** - Both success and failure scenarios
5. **Cleanup** - Automatic rollback after each test

## Test Categories

### Page Tests (test_pages.py)

```python
TestPageCreation          # Creating pages with various options
TestPageRetrieval         # Getting pages by ID, slug, etc.
TestPageUpdate            # Updating page content and metadata
TestPageDeletion          # Soft/hard delete and restore
TestPageListing           # Filtering and pagination
TestPageTree              # Hierarchical page structures
TestPageMetadata          # View counts, paths, etc.
TestPageSlugGeneration    # Slug creation and normalization
```

### Versioning Tests (test_versioning.py)

```python
TestVersionHistory        # Retrieving version history
TestVersionComparison     # Comparing versions and diffs
TestVersionRollback       # Rolling back to previous versions
TestVersionTimeline       # Timeline visualization
TestVersionPruning        # Cleaning up old versions
TestDiffCalculations      # Diff algorithm testing
```

### Search Tests (test_search.py)

```python
TestBasicSearch          # Basic text searching
TestSearchFilters        # Category, status, tag filters
TestSearchPagination     # Result pagination
TestSearchOrdering       # Relevance, date, title ordering
TestFullTextSearch       # Full-text search capabilities
TestSearchByTags         # Tag-based searching
TestSearchByCategory     # Category-based searching
TestAdvancedSearch       # Multi-criteria searching
TestSimilarPages         # Finding related pages
TestSearchSuggestions    # Autocomplete suggestions
TestSearchScoring        # Relevance scoring
TestSearchHighlights     # Result highlighting
```

### Permission Tests (test_permissions.py)

```python
TestPagePermissions           # Page-level permissions
TestPermissionRevocation      # Removing permissions
TestPermissionChecking        # Verifying access
TestEffectivePermissions      # Computing final permissions
TestCategoryPermissions       # Category-level permissions
TestNamespacePermissions      # Namespace access control
TestBulkPermissionOperations  # Bulk operations
TestPermissionAuditing        # Audit and cleanup
```

### Category Tests (test_categories.py)

```python
TestCategoryCreation          # Creating categories
TestCategoryRetrieval         # Getting categories
TestCategoryUpdate            # Updating categories
TestCategoryDeletion          # Deleting categories
TestCategoryTree              # Hierarchy and breadcrumbs
TestCategoryPageCounts        # Page counting
TestTagCreation               # Creating tags
TestTagRetrieval              # Getting tags
TestTagCloud                  # Tag cloud generation
TestTagSuggestions            # Auto-suggesting tags
TestAutoCategorization        # Auto-categorizing pages
TestTagMerging                # Merging duplicate tags
TestCircularReferenceDetection # Preventing cycles
```

## Key Testing Features

### 1. Transaction Isolation

Each test runs in its own transaction that's rolled back after completion:

```python
@pytest.fixture(scope='function')
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()  # Automatic cleanup
    connection.close()
```

### 2. Factory Pattern

Easily create test data with customization:

```python
def test_example(page_factory):
    page = page_factory(
        title='Custom Title',
        status=PageStatus.PUBLISHED
    )
    assert page.title == 'Custom Title'
```

### 3. Comprehensive Coverage

Tests cover:
- ✅ Happy path scenarios
- ✅ Error handling
- ✅ Edge cases
- ✅ Boundary conditions
- ✅ Data validation
- ✅ Database constraints
- ✅ Business logic

### 4. Realistic Test Data

Uses realistic data patterns:
- Proper slug generation
- Valid dates and timestamps
- Realistic content and titles
- Proper relationships

## Best Practices

### Writing New Tests

1. **Use descriptive names**
   ```python
   def test_create_page_with_valid_data(self):  # Good
   def test_page_1(self):  # Bad
   ```

2. **Include docstrings**
   ```python
   def test_search_by_tags(self):
       """Test that search correctly filters by tags."""
   ```

3. **Use fixtures for setup**
   ```python
   def test_update_page(self, sample_page):
       # sample_page is already created and cleaned up
   ```

4. **Test one thing at a time**
   ```python
   def test_page_title_update(self):
       # Only test title updates
   ```

5. **Use assertions effectively**
   ```python
   assert page.title == 'Expected Title'
   assert len(results) > 0
   assert page_id in accessible_ids
   ```

## Common Patterns

### Testing CRUD Operations

```python
def test_create_read_update_delete(db_session, mock_user):
    service = PageManager(db_session)

    # Create
    page = service.create_page(request, author_id=mock_user['id'])
    assert page.id is not None

    # Read
    retrieved = service.get_page(page.id)
    assert retrieved.title == page.title

    # Update
    updated = service.update_page(page.id, update_request, user_id=mock_user['id'])
    assert updated.title == 'New Title'

    # Delete
    success = service.delete_page(page.id, user_id=mock_user['id'])
    assert success
```

### Testing Permissions

```python
def test_permission_check(db_session, sample_page, mock_user):
    service = PermissionService(db_session)

    # Grant permission
    service.grant_page_permission(
        page_id=sample_page.id,
        user_id=mock_user['id'],
        permission_level=PermissionLevel.EDIT
    )

    # Verify
    has_access = service.check_page_permission(
        page_id=sample_page.id,
        user_id=mock_user['id'],
        required_level=PermissionLevel.EDIT
    )

    assert has_access
```

### Testing Search

```python
def test_search_with_filters(db_session, sample_pages):
    service = SearchService(db_session)

    results, total = service.search(
        query='python',
        filters={
            'status': PageStatus.PUBLISHED,
            'tags': ['tutorial']
        }
    )

    assert total > 0
    assert all(r['page'].status == PageStatus.PUBLISHED for r in results)
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest modules/wiki/tests/ \
      --cov=modules.wiki \
      --cov-report=xml \
      --junitxml=test-results.xml
```

## Troubleshooting

### Import Errors

If you encounter import errors, ensure the project root is in PYTHONPATH:

```bash
export PYTHONPATH=/home/user/nexus-platform:$PYTHONPATH
pytest tests/
```

### Database Errors

Tests use SQLite in-memory database. If you see database errors:

1. Check that `database.py` exists and exports `Base`
2. Ensure SQLAlchemy is installed
3. Verify model imports

### Fixture Errors

If fixtures aren't found:

1. Ensure `conftest.py` is in the tests directory
2. Check that pytest discovers the tests directory
3. Run with `-v` flag for verbose output

## Performance

- Average test execution time: ~0.01-0.05s per test
- Full suite execution: ~10-20 seconds
- Uses in-memory SQLite for speed
- Transaction rollback provides fast cleanup

## Maintenance

### Adding New Tests

1. Add test to appropriate test file
2. Use existing fixtures when possible
3. Follow naming conventions
4. Include docstring
5. Test both success and failure cases

### Updating Fixtures

When updating fixtures in `conftest.py`:

1. Document the change
2. Update dependent tests
3. Ensure backward compatibility
4. Run full test suite

## License

Part of the NEXUS Platform project.

## Authors

NEXUS Platform Team

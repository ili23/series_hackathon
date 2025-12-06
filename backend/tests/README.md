# Database Tests

## Running Tests

Install dependencies:
```bash
pip install pytest pytest-cov
```

Run all tests:
```bash
pytest backend/tests/
```

Run with coverage:
```bash
pytest backend/tests/ --cov=backend.db --cov-report=html
```

Run specific test file:
```bash
pytest backend/tests/test_db_accessors.py
```

Run specific test:
```bash
pytest backend/tests/test_db_accessors.py::TestAddToUserTable::test_add_new_user
```

## Test Structure

- `conftest.py` - Pytest fixtures for database setup
- `test_db_accessors.py` - Tests for all accessor functions

## Test Coverage

Tests cover:
- Adding users
- Updating users
- Adding languages
- Adding voice messages
- Querying users by language
- Database relationships


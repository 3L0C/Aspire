# Aspire Application Testing

This directory contains tests for the Aspire goal-tracking application. The tests are organized into unit tests and functional tests.

## Test Structure

- `conftest.py`: Contains pytest fixtures for setting up test environments
- `test_config.py`: Tests for application configuration
- `unit/`: Unit tests for individual components
  - `test_models.py`: Tests for database models
  - `test_services.py`: Tests for service classes
- `functional/`: Functional tests for application routes and user flows
  - `test_auth.py`: Tests for authentication functionality
  - `test_goals.py`: Tests for goal management
  - `test_tasks.py`: Tests for task management

## Running Tests

To run all tests:

```bash
# Install test dependencies
pip install -r test-requirements.txt

# Run tests
pytest
```

To run tests with coverage report:

```bash
pytest --cov=app --cov-report=html
```

To run a specific test file:

```bash
pytest tests/unit/test_models.py
```

To run a specific test function:

```bash
pytest tests/unit/test_models.py::test_user_password_hashing
```

## Test Fixtures

The test fixtures in `conftest.py` provide:

- `app`: A Flask application configured for testing
- `client`: A Flask test client
- `_db`: A database session
- `test_user`: A pre-created user for authentication tests
- `auth_client`: A test client with authentication
- `test_goal`: A pre-created goal for goal-related tests
- `test_task`: A pre-created task for task-related tests

These fixtures can be used in test functions by including them as parameters.

## Writing New Tests

When writing new tests:

1. Choose the appropriate location (unit or functional)
2. Use existing fixtures when possible
3. Follow the pattern of existing tests
4. Make sure tests are independent and don't rely on state from other tests
5. Use meaningful assert statements with helpful error messages

## Test Coverage

The test configuration includes coverage reporting, which identifies which parts of the application code are executed during tests. Aim for high coverage, especially in critical components.

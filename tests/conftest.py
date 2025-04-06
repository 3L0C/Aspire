import os
import sys
import pytest
import tempfile

# Add the project root directory to the Python path
# This allows importing the app package from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import app
from app import create_app, db
from app.data.models.user import User
from app.data.models.goal import Goal, LongTermGoal, ShortTermGoal
from app.data.models.task import Task, OneTimeTask, RecurringTask


@pytest.fixture(scope='function')
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()

    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF protection for testing
        'SECRET_KEY': 'test-key'
    }

    app = create_app(test_config)

    # Create the database and tables
    with app.app_context():
        db.create_all()

    yield app

    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def _db(app):
    """Create and yield a database session."""
    with app.app_context():
        yield db


@pytest.fixture(scope='function')
def test_user(_db):
    """Create a test user for authentication tests."""
    user = User(username='testuser', email='test@example.com')
    user.set_password('password')

    # Create a profile for the user
    user.manage_profile()

    _db.session.add(user)
    _db.session.commit()

    return user


@pytest.fixture(scope='function')
def auth_client(client, test_user):
    """A test client with authentication."""
    # Login using the Flask test client without the context manager
    response = client.post(
        '/login',
        data={
            'username': 'testuser',
            'password': 'password',
            'remember_me': False
        },
        follow_redirects=True
    )

    # Just check status code instead of content for fixture
    assert response.status_code == 200

    return client


@pytest.fixture(scope='function')
def test_goal(_db, test_user):
    """Create a test long-term goal."""
    goal = LongTermGoal(
        title="Test Long-term Goal",
        description="This is a test goal",
        user_id=test_user.id,
        timeframe="1 year"
    )
    _db.session.add(goal)
    _db.session.commit()

    return goal


@pytest.fixture(scope='function')
def test_task(_db, test_user, test_goal):
    """Create a test task linked to a goal."""
    task = OneTimeTask(
        title="Test Task",
        description="This is a test task",
        user_id=test_user.id,
        priority="Medium"
    )
    _db.session.add(task)
    _db.session.commit()

    task.link_to_goal(test_goal)
    _db.session.commit()

    return task

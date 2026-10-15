"""Pytest configuration and fixtures for the AI Educational Platform tests."""
import os
import tempfile

# Set environment variables BEFORE importing any app modules
# This ensures the test database and mock LLM are used
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "sklearn"
os.environ["EMBEDDING_MODEL"] = "tfidf"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["MAX_UPLOAD_SIZE_MB"] = "20"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole, UserPreference
from app.core.security import hash_password, create_access_token
from app.rag.vector_store import InMemoryVectorStore, set_vector_store


# Create test database engine
_test_engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests and drop them after."""
    # Set up in-memory vector store for tests
    set_vector_store(InMemoryVectorStore())

    # Create tables
    Base.metadata.create_all(bind=_test_engine)
    yield
    # Cleanup
    Base.metadata.drop_all(bind=_test_engine)
    os.close(_test_db_fd)
    try:
        os.unlink(_test_db_path)
    except OSError:
        pass


@pytest.fixture
def db_session():
    """Provide a database session for a single test with automatic cleanup."""
    session = TestSessionLocal()
    # Clean all tables before each test
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_user(db_session):
    """Create and return a test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        role=UserRole.student,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    prefs = UserPreference(
        user_id=user.id,
        preferred_subjects='["mathematics", "physics"]',
        default_answer_style="detailed",
        learning_goals="Master calculus",
    )
    db_session.add(prefs)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_2(db_session):
    """Create a second test user for ownership tests."""
    user = User(
        email="other@example.com",
        hashed_password=hash_password("otherpassword123"),
        full_name="Other User",
        role=UserRole.student,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create and return an admin user."""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        full_name="Admin User",
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user):
    """Create a JWT token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def test_user_2_token(test_user_2):
    """Create a JWT token for the second test user."""
    return create_access_token(data={"sub": str(test_user_2.id)})


@pytest.fixture
def admin_token(admin_user):
    """Create a JWT token for the admin user."""
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture
def client(db_session):
    """Provide a TestClient with overridden get_db dependency."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_user(db_session, test_user):
    """Provide a TestClient authenticated as the test user (bypasses token check)."""
    from app.core.dependencies import get_current_active_user

    def override_get_current_user():
        return test_user

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

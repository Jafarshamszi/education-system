"""
Test configuration and fixtures for the Education Management System
"""

import pytest
import uuid
from typing import Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models import User, Person
from app.auth.password import hash_password
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.dialects.postgresql import JSONB, UUID

def visit_JSONB(self, type_, **kw):
    return "JSON"

def visit_ARRAY(self, type_, **kw):
    return "JSON"

def visit_UUID(self, type_, **kw):
    return "VARCHAR(36)"

SQLiteTypeCompiler.visit_JSONB = visit_JSONB
SQLiteTypeCompiler.visit_ARRAY = visit_ARRAY
SQLiteTypeCompiler.visit_UUID = visit_UUID

# Test database URL (SQLite in-memory for testing)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

# Create test engine
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable foreign key support for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Test session maker
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


def get_test_db():
    """Get test database session"""
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


@pytest.fixture(scope="session")
def setup_test_db():
    """Create test database tables"""
    # Sanitize models for SQLite
    import uuid
    from sqlalchemy.sql.elements import TextClause
    from sqlalchemy.schema import ColumnDefault
    
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is not None:
                if hasattr(column.server_default, 'arg'):
                    # Handle string arguments
                    if isinstance(column.server_default.arg, str):
                        sql = column.server_default.arg
                        if '::jsonb' in sql:
                            column.server_default.arg = sql.replace('::jsonb', '')
                        if 'gen_random_uuid()' in sql:
                            column.server_default = None
                            # column.default = ColumnDefault(uuid.uuid4) - causing issues with create_all
                    
                    # Handle TextClause arguments (from text("..."))
                    elif isinstance(column.server_default.arg, TextClause):
                        sql = column.server_default.arg.text
                        if '::jsonb' in sql:
                            # Create a new TextClause with the sanitized SQL
                            from sqlalchemy import text
                            column.server_default.arg = text(sql.replace('::jsonb', ''))
                        
                        if 'gen_random_uuid()' in sql:
                            column.server_default = None
                            # column.default = ColumnDefault(uuid.uuid4)

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(setup_test_db):
    """Create a fresh database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(setup_test_db):
    """Create test client with dependency override"""
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Test entity creation helpers
def create_test_person(session, **kwargs):
    """Create a test person"""
    default_data = {
        "id": uuid.uuid4(),
        "first_name": "Test",
        "last_name": "User",
    }
    default_data.update(kwargs)
    
    person = Person(**default_data)
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


def create_test_user(session, person=None, **kwargs):
    """Create a test user"""
    # Filter out keys that are not in User model
    user_data = {
        "id": uuid.uuid4(),
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password_hash": hash_password("testpass123"),
        "is_active": True
    }
    
    # Handle user_type if passed (ignore it for now as User model doesn't have it)
    user_type = None
    if "user_type" in kwargs:
        user_type = kwargs.pop("user_type")
        
    user_data.update(kwargs)
    
    user = User(**user_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    
    if user_type:
        user.user_type = user_type
    
    if person:
        person.user_id = user.id
        session.add(person)
        session.commit()
        session.refresh(person)
        
    if user_type and user_type.upper() == "STUDENT":
        if not person:
            # Create person if not exists
            person = create_test_person(session)
            person.user_id = user.id
            session.add(person)
            session.commit()
            session.refresh(person)
            
        from app.models import Student
        student = Student(
            id=uuid.uuid4(),
            user_id=user.id,
            person_id=person.id
        )
        session.add(student)
        session.commit()
        
    elif user_type and user_type.upper() in ["TEACHER", "ADMIN"]:
        from app.models.staff_member import StaffMember
        from datetime import datetime
        
        admin_role = None
        if user_type.upper() == "ADMIN":
            admin_role = "head_of_department"
            
        staff = StaffMember(
            id=uuid.uuid4(),
            user_id=user.id,
            employee_number=f"EMP{uuid.uuid4().hex[:6]}",
            position_title={"en": "Lecturer"},
            hire_date=datetime.now().date(),
            administrative_role=admin_role,
            academic_rank="lecturer"
        )
        session.add(staff)
        session.commit()
        
    return user
    pass


from typing import Any


class AuthenticatedTestClient:
    """Test client with authentication helpers"""
    
    def __init__(self, client: TestClient, session):
        self.client = client
        self.session = session
        self._token = None
        self.user: Any = None
    
    @property
    def token(self):
        if not self._token and self.user:
            from app.auth.jwt_handler import create_access_token
            user_type = getattr(self.user, "user_type", "STUDENT")
            token_data = {
                "sub": str(self.user.id),
                "user_type": user_type,
                "username": self.user.username
            }
            self._token = create_access_token(data=token_data)
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    def login(self, username: str = "testuser", password: str = "testpass123"):
        """Login and store token"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return True
        return False
    
    def get_headers(self):
        """Get authorization headers"""
        if not self.token:
            raise ValueError("No token available. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}
    
    def get(self, url, **kwargs):
        """GET request with auth"""
        return self.client.get(url, headers=self.get_headers(), **kwargs)
    
    def post(self, url, **kwargs):
        """POST request with auth"""
        return self.client.post(url, headers=self.get_headers(), **kwargs)


# Authentication fixtures for different user types
@pytest.fixture
def auth_client(client, db_session):
    """Authenticated client with test user"""
    # Create user
    user = create_test_user(db_session)
    
    auth_client_instance = AuthenticatedTestClient(client, db_session)
    auth_client_instance.user = user
    return auth_client_instance


@pytest.fixture
def student_client(client, db_session):
    """Authenticated client as student"""
    user = create_test_user(
        db_session, 
        username="student", 
        email="student@example.com",
        user_type="student"
    )
    
    auth_client_instance = AuthenticatedTestClient(client, db_session)
    auth_client_instance.user = user
    return auth_client_instance


@pytest.fixture
def teacher_client(client, db_session):
    """Authenticated client as teacher"""
    user = create_test_user(
        db_session, 
        username="teacher", 
        email="teacher@example.com",
        user_type="teacher"
    )
    
    auth_client_instance = AuthenticatedTestClient(client, db_session)
    auth_client_instance.user = user
    return auth_client_instance


@pytest.fixture
def admin_client(client, db_session):
    """Authenticated client as admin"""
    user = create_test_user(
        db_session, 
        username="admin", 
        email="admin@example.com",
        user_type="admin"
    )
    
    auth_client_instance = AuthenticatedTestClient(client, db_session)
    auth_client_instance.user = user
    return auth_client_instance


@pytest.fixture
def authenticated_student(student_client):
    return student_client


@pytest.fixture
def authenticated_teacher(teacher_client):
    return teacher_client


@pytest.fixture
def authenticated_admin(admin_client):
    return admin_client

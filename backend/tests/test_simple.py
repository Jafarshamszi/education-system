"""
Simple tests to validate basic functionality
"""


def test_basic_functionality():
    """Test basic Python functionality"""
    assert 1 + 1 == 2


def test_imports():
    """Test that we can import the main modules"""
    from app.main import app
    from app.models import Person, Account, User
    from app.auth.password import hash_password
    
    assert app is not None
    assert Person is not None
    assert Account is not None
    assert User is not None
    assert hash_password is not None


def test_app_creation():
    """Test FastAPI app creation"""
    from app.main import app
    
    assert app.title == "Education Management System"


def test_password_hashing():
    """Test password hashing works"""
    from app.auth.password import hash_password, verify_password
    
    password = "test123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_database_models_can_be_created():
    """Test that models can be instantiated"""
    from app.models import Person, Account
    
    # Test creating model instances (no database required)
    person = Person(first_name="John", last_name="Doe")
    assert person.first_name == "John"
    assert person.last_name == "Doe"
    
    account = Account(username="testuser", email="test@example.com")
    assert account.username == "testuser"
    assert account.email == "test@example.com"


def test_api_routes_exist():
    """Test that API routes are defined"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    
    # Test API health endpoint
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()

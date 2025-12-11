# Database Troubleshooting Quick Reference

## Common Database Errors and Solutions

### 🔥 Most Common Issues

#### 1. `NOT NULL constraint failed: [table].id`
**Quick Fix**: Add autoincrement to model definition
```python
# Before (broken)
id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

# After (fixed)
id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
```

#### 2. `FOREIGN KEY constraint failed`
**Quick Fix**: Enable foreign keys in SQLite
```python
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

#### 3. `TypeError: 'field_name' is an invalid keyword argument`
**Quick Fix**: Check field names in model vs usage
```python
# Model has 'birthdate' but code uses 'birth_date'
person = Person(birthdate="1990-01-01")  # ✅ Correct
person = Person(birth_date="1990-01-01")  # ❌ Wrong
```

---

## 🛠️ Database Model Fixes

### Standard Model Template
```python
from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

class ModelName(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "table_name"
    
    # Always include autoincrement for primary keys
    id: Mapped[int] = mapped_column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True
    )
    
    # Nullable fields
    field_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Required fields
    required_field: Mapped[str] = mapped_column(Text, nullable=False)
```

---

## 🧪 Test Database Setup

### Correct SQLite Test Configuration
```python
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
```

---

## 🔍 Debugging Commands

### Check Database Schema
```python
# In Python shell or test
from sqlalchemy import inspect
from app.core.database import engine

inspector = inspect(engine)
print("Tables:", inspector.get_table_names())

# Check specific table
columns = inspector.get_columns('persons')
for col in columns:
    print(f"{col['name']}: {col['type']} (nullable: {col['nullable']})")
```

### Test Model Creation
```python
# Test if model can be created without database
from app.models import Person

# This should work (no database needed)
person = Person(firstname="Test", lastname="User")
print(person.firstname)  # Should print "Test"
```

### Check Foreign Key Support
```python
# Run this in test environment
import sqlite3
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys")
result = cursor.fetchone()
print(f"Foreign keys enabled: {result[0] == 1}")
```

---

## ⚡ Quick Fixes for Immediate Testing

### 1. Bypass ID Issues (Temporary)
```python
# In test factories, provide explicit IDs
def create_test_person(session, **kwargs):
    import uuid
    default_data = {
        "id": abs(hash(str(uuid.uuid4()))) % (10**8),  # Generate ID
        "firstname": "Test",
        "lastname": "User",
        "active": 1
    }
    default_data.update(kwargs)
    return Person(**default_data)
```

### 2. Simple Test Without Database
```python
def test_model_properties():
    """Test model without database operations"""
    person = Person(firstname="John", lastname="Doe")
    assert person.firstname == "John"
    assert person.lastname == "Doe"
    # Don't call session.add() or commit()
```

### 3. Mock Database Operations
```python
from unittest.mock import Mock

def test_with_mock_db():
    mock_session = Mock()
    # Test business logic without real database
    service = UserService(mock_session)
    result = service.create_user_data({"name": "test"})
    assert result is not None
```

---

## 📋 Checklist Before Running Tests

- [ ] All models have `autoincrement=True` on primary keys
- [ ] SQLite foreign keys are enabled in test config
- [ ] Test database uses in-memory SQLite (`:memory:`)
- [ ] Model field names match between definition and usage
- [ ] Session management is properly configured
- [ ] Base.metadata.create_all() is called in test setup

---

## 🚨 Emergency Test Commands

If tests are completely broken, run these to verify basic functionality:

```bash
# Test 1: Can we import models?
python -c "from app.models import Person, User, Account; print('✅ Models import OK')"

# Test 2: Can we create model instances?
python -c "from app.models import Person; p = Person(firstname='Test'); print('✅ Model creation OK')"

# Test 3: Can we start the app?
python -c "from app.main import app; print('✅ App creation OK')"

# Test 4: Are routes available?
python -c "from fastapi.testclient import TestClient; from app.main import app; c = TestClient(app); r = c.get('/health'); print(f'✅ Health endpoint: {r.status_code}')"
```

If any of these fail, fix them before running full test suites.
"""
Tests for authentication endpoints
"""

import pytest
from fastapi import status
from app.auth.password import hash_password


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_login_success(self, client, db_session):
        """Test successful login"""
        # Create test entities
        from tests.conftest import create_test_user
        user = create_test_user(db_session)
        
        # Login
        response = client.post("/api/v1/auth/login", json={
            "username": user.username,
            "password": "testpass123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # assert data["user_id"] == str(user.id)
        assert data["username"] == user.username

    def test_login_invalid_username(self, client):
        """Test login with invalid username"""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_invalid_password(self, client, db_session):
        """Test login with invalid password"""
        # Create test entities
        from tests.conftest import create_test_user
        user = create_test_user(db_session)
        
        # Login with wrong password
        response = client.post("/api/v1/auth/login", json={
            "username": user.username,
            "password": "wrongpassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_inactive_account(self, client, db_session):
        """Test login with inactive account"""
        # Create test entities
        from tests.conftest import create_test_user
        user = create_test_user(db_session)
        
        # Deactivate account
        user.is_active = False
        db_session.commit()
        
        # Login
        response = client.post("/api/v1/auth/login", json={
            "username": user.username,
            "password": "testpass123"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User account is disabled or locked" in response.json()["detail"]

    def test_login_blocked_user(self, client, db_session):
        """Test login with blocked user"""
        # Create test entities
        from tests.conftest import create_test_user
        user = create_test_user(db_session)
        
        # Block user
        user.is_locked = True
        db_session.commit()
        
        # Login
        response = client.post("/api/v1/auth/login", json={
            "username": user.username,
            "password": "testpass123"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User account is disabled or locked" in response.json()["detail"]

    def test_get_current_user_profile(self, authenticated_student):
        """Test getting current user profile"""
        response = authenticated_student.get("/api/v1/auth/me")
    
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "user_type" in data
        assert "email" in data
        assert data["user_type"] == "STUDENT"

    def test_get_current_user_profile_unauthorized(self, client):
        """Test getting profile without authentication"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, authenticated_student):
        """Test token refresh"""
        response = authenticated_student.post("/api/v1/auth/refresh")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_unauthorized(self, client):
        """Test token refresh without authentication"""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token(self, client):
        """Test endpoints with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_legacy_password_compatibility(self, client, db_session):
        """Test legacy password compatibility"""
        from app.models import User
        import uuid
        
        password = "legacypass123"
        
        user = User(
            id=uuid.uuid4(),
            username="legacyuser",
            email="legacy@example.com",
            password_hash=password,  # Stored as plain text
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Test login with legacy password
        response = client.post("/api/v1/auth/login", json={
            "username": "legacyuser",
            "password": password
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        
        # Verify password was upgraded
        db_session.refresh(user)
        assert user.password_hash.startswith("$2")


class TestPasswordSecurity:
    """Test password hashing and verification"""

    def test_password_hashing(self):
        """Test password hashing"""
        from app.auth.password import verify_password
        
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_legacy_password_verification(self):
        """Test legacy base64 password verification"""
        import base64
        from app.auth.password import verify_legacy_password
        
        password = "testpassword123"
        encoded = base64.b64encode(password.encode()).decode()
        
        assert verify_legacy_password(password, encoded)
        assert not verify_legacy_password("wrongpassword", encoded)


class TestJWTTokens:
    """Test JWT token handling"""

    def test_jwt_token_creation(self):
        """Test JWT token creation"""
        from app.auth.jwt_handler import create_access_token
        from datetime import timedelta
        
        data = {"sub": "123", "user_type": "STUDENT"}
        token = create_access_token(data, timedelta(minutes=30))
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_jwt_token_verification(self):
        """Test JWT token verification"""
        from app.auth.jwt_handler import create_access_token, verify_token
        from datetime import timedelta
        
        data = {"sub": "123", "user_type": "STUDENT"}
        token = create_access_token(data, timedelta(minutes=30))
        
        payload = verify_token(token)
        assert payload["sub"] == "123"
        assert payload["user_type"] == "STUDENT"

    def test_invalid_jwt_token(self):
        """Test invalid JWT token handling"""
        from app.auth.jwt_handler import verify_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            verify_token("invalid_token")

    def test_expired_jwt_token(self):
        """Test expired JWT token handling"""
        from app.auth.jwt_handler import create_access_token, verify_token
        from datetime import timedelta
        from fastapi import HTTPException
        import time
        
        # Create token that expires immediately
        data = {"sub": "123", "user_type": "STUDENT"}
        token = create_access_token(data, timedelta(seconds=-1))
        
        # Wait a bit to ensure expiration
        time.sleep(0.1)
        
        with pytest.raises(HTTPException):
            verify_token(token)

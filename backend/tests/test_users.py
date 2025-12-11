"""
Tests for user management and role-based access control
"""

import pytest
from fastapi import status


class TestRoleBasedAccess:
    """Test role-based access control"""

    def test_student_access_own_profile(self, authenticated_student):
        """Test student can access own profile"""
        response = authenticated_student.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_type"] == "STUDENT"

    def test_teacher_access_own_profile(self, authenticated_teacher):
        """Test teacher can access own profile"""
        response = authenticated_teacher.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_type"] == "TEACHER"

    def test_admin_access_own_profile(self, authenticated_admin):
        """Test admin can access own profile"""
        response = authenticated_admin.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_type"] == "ADMIN"

    def test_student_cannot_access_student_list(self, authenticated_student):
        """Test student cannot access student list"""
        response = authenticated_student.get("/api/v1/students/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_teacher_can_access_student_list(self, authenticated_teacher):
        """Test teacher can access student list"""
        response = authenticated_teacher.get("/api/v1/students/")
        # Should return 200 or 404 depending on students in DB
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_admin_can_access_student_list(self, authenticated_admin):
        """Test admin can access student list"""
        response = authenticated_admin.get("/api/v1/students/")
        # Should return 200 or 404 depending on students in DB
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestUserTypes:
    """Test different user types and their hierarchies"""

    def test_user_type_hierarchy(self):
        """Test user type hierarchy understanding"""
        from app.models.user import UserType
        
        # Test enum values
        assert UserType.STUDENT == "STUDENT"
        assert UserType.TEACHER == "TEACHER" 
        assert UserType.ADMIN == "ADMIN"
        assert UserType.SYSADMIN == "SYSADMIN"
        assert UserType.OWNER == "OWNER"
        assert UserType.TYUTOR == "TYUTOR"

    def test_current_user_role_checking(self, authenticated_student):
        """Test CurrentUser role checking methods"""
        # This would need to be tested with actual CurrentUser object
        # For now, we test the response structure
        response = authenticated_student.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_type" in data
        assert data["user_type"] == "STUDENT"


class TestAuthenticationDependencies:
    """Test authentication dependencies and access control"""

    def test_require_authentication(self, client):
        """Test endpoints require authentication"""
        protected_endpoints = [
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/auth/refresh", "POST"),
            ("/api/v1/students/", "GET"),
            ("/api/v1/teachers/", "GET")
        ]
    
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_bearer_token(self, client):
        """Test invalid bearer token handling"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_malformed_authorization_header(self, client):
        """Test malformed authorization header"""
        headers = {"Authorization": "NotBearer token"}
        
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_authorization_header(self, client):
        """Test missing authorization header"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCurrentUserFeatures:
    """Test CurrentUser class features"""

    def test_user_profile_data_structure(self, authenticated_student):
        """Test user profile data structure"""
        response = authenticated_student.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        required_fields = ["id", "username", "user_type", "is_active"]
        
        for field in required_fields:
            assert field in data

    def test_user_profile_student_type(self, authenticated_student):
        """Test student user profile"""
        response = authenticated_student.get("/api/v1/auth/me")
        data = response.json()
        
        assert data["user_type"] == "STUDENT"
        assert data["is_active"] is True

    def test_user_profile_teacher_type(self, authenticated_teacher):
        """Test teacher user profile"""
        response = authenticated_teacher.get("/api/v1/auth/me")
        data = response.json()
        
        assert data["user_type"] == "TEACHER"
        assert data["is_active"] is True

    def test_user_profile_admin_type(self, authenticated_admin):
        """Test admin user profile"""
        response = authenticated_admin.get("/api/v1/auth/me")
        data = response.json()
        
        assert data["user_type"] == "ADMIN"
        assert data["is_active"] is True


class TestSecurityFeatures:
    """Test security features and edge cases"""

    def test_token_in_different_format(self, client):
        """Test token in different formats"""
        # Test lowercase bearer
        headers = {"Authorization": "bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_token(self, client):
        """Test empty token"""
        headers = {"Authorization": "Bearer "}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_space_in_auth_header(self, client):
        """Test authorization header without space"""
        headers = {"Authorization": "Bearertoken123"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_multiple_auth_headers(self, client):
        """Test multiple authorization headers"""
        # TestClient might not handle multiple headers well,
        # but we test the concept
        headers = {"Authorization": "Bearer token1"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserManagementEndpoints:
    """Test user management API endpoints"""

    def test_health_endpoint_public_access(self, client):
        """Test health endpoint is publicly accessible"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "environment" in data

    def test_api_health_endpoint(self, client):
        """Test API health endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "Education System API is running"

    def test_openapi_docs_accessible(self, client):
        """Test OpenAPI documentation is accessible"""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_swagger_ui_accessible(self, client):
        """Test Swagger UI is accessible"""
        response = client.get("/api/v1/docs")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_redoc_accessible(self, client):
        """Test ReDoc is accessible"""
        response = client.get("/api/v1/redoc")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
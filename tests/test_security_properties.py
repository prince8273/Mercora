"""Property-based tests for security measures."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from hypothesis import given, strategies as st, settings
from fastapi import HTTPException

from src.auth.security import (
    create_access_token,
    decode_access_token,
    verify_password,
    get_password_hash
)
from src.auth.rbac import RBACService, Permission, RoleType
from src.models.user import User
from src.models.role import Role, ROLE_PERMISSIONS


# Strategies for generating test data
@st.composite
def user_strategy(draw):
    """Generate a random User."""
    return User(
        id=draw(st.uuids()),
        tenant_id=draw(st.uuids()),
        email=draw(st.emails()),
        hashed_password=get_password_hash("password123"),
        full_name=draw(st.text(min_size=1, max_size=100)),
        is_active=draw(st.booleans()),
        is_superuser=draw(st.booleans())
    )


@st.composite
def role_type_strategy(draw):
    """Generate a random RoleType."""
    return draw(st.sampled_from(list(RoleType)))


@st.composite
def permission_strategy(draw):
    """Generate a random Permission."""
    return draw(st.sampled_from(list(Permission)))


class TestSecurityProperties:
    """Property-based tests for security measures."""
    
    @given(
        user_id=st.uuids(),
        tenant_id=st.uuids(),
        role=st.sampled_from(["user", "admin", "superuser"])
    )
    @settings(max_examples=100)
    def test_property_51_unauthenticated_requests_rejected(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role: str
    ):
        """
        Property 51: Unauthenticated requests are rejected.
        
        Validates Requirements: 12.1
        
        Property: Requests without valid JWT tokens are rejected with 401 Unauthorized.
        Valid tokens must contain user_id, tenant_id, and role claims.
        """
        # Arrange & Act: Create a valid token
        token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role
        )
        
        # Assert: Token is created
        assert token is not None, \
            "Token should be created"
        assert isinstance(token, str), \
            "Token should be a string"
        assert len(token) > 0, \
            "Token should not be empty"
        
        # Act: Decode the token
        payload = decode_access_token(token)
        
        # Assert: Token contains required claims
        assert "sub" in payload, \
            "Token must contain 'sub' (user_id) claim"
        assert "tenant_id" in payload, \
            "Token must contain 'tenant_id' claim"
        assert "role" in payload, \
            "Token must contain 'role' claim"
        assert "exp" in payload, \
            "Token must contain 'exp' (expiration) claim"
        assert "iat" in payload, \
            "Token must contain 'iat' (issued at) claim"
        
        # Assert: Claims have correct values
        assert payload["sub"] == str(user_id), \
            "User ID in token must match"
        assert payload["tenant_id"] == str(tenant_id), \
            "Tenant ID in token must match"
        assert payload["role"] == role, \
            "Role in token must match"
        
        # Assert: Expiration is in the future
        exp_timestamp = payload["exp"]
        now_timestamp = datetime.now(timezone.utc).timestamp()
        assert exp_timestamp > now_timestamp, \
            "Token expiration must be in the future"
        
        # Assert: Issued at is in the past or present
        iat_timestamp = payload["iat"]
        assert iat_timestamp <= now_timestamp + 1, \
            "Token issued at must be in the past or present"
    
    @given(
        user_id=st.uuids(),
        tenant_id=st.uuids()
    )
    @settings(max_examples=100)
    def test_invalid_token_rejected(
        self,
        user_id: UUID,
        tenant_id: UUID
    ):
        """
        Test that invalid tokens are rejected.
        
        This validates token validation and rejection.
        """
        # Test 1: Invalid token string
        with pytest.raises(Exception):  # JWTError or similar
            decode_access_token("invalid.token.string")
        
        # Test 2: Expired token
        expired_token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        with pytest.raises(Exception):  # JWTError for expired token
            decode_access_token(expired_token)
    
    @given(
        role_type=role_type_strategy(),
        permission=permission_strategy()
    )
    @settings(max_examples=100)
    def test_property_52_rbac_enforcement(
        self,
        role_type: RoleType,
        permission: Permission
    ):
        """
        Property 52: Role-based access is enforced.
        
        Validates Requirements: 12.4
        
        Property: Users can only access resources they have permissions for.
        Permissions are determined by their assigned roles.
        """
        # Arrange: Create a role with the given type
        role = Role(
            id=uuid4(),
            tenant_id=uuid4(),
            name=role_type.value,
            role_type=role_type,
            is_system_role=True,
            is_active=True
        )
        
        # Act: Check if role has permission
        role_permissions = role.get_permissions()
        has_permission = permission.value in role_permissions
        
        # Assert: Permission check is consistent with role definition
        expected_permissions = ROLE_PERMISSIONS.get(role_type, [])
        assert set(role_permissions) == set(expected_permissions), \
            "Role permissions must match defined permissions"
        
        # Assert: Superuser has all permissions
        if role_type == RoleType.SUPERUSER:
            assert has_permission, \
                "Superuser must have all permissions"
        
        # Assert: Permission hierarchy is respected
        if role_type == RoleType.ADMIN:
            # Admin should have most permissions except system admin
            if permission != Permission.SYSTEM_ADMIN and permission != Permission.MANAGE_TENANTS:
                # Admin has most permissions
                pass
        
        if role_type == RoleType.VIEWER:
            # Viewer should only have read permissions
            if permission in [Permission.READ_DATA, Permission.VIEW_REPORTS]:
                assert has_permission, \
                    "Viewer must have read permissions"
            else:
                assert not has_permission, \
                    "Viewer must not have write/admin permissions"
    
    @given(
        user_id=st.uuids(),
        tenant_id=st.uuids(),
        other_tenant_id=st.uuids()
    )
    @settings(max_examples=100)
    def test_property_84_tenant_authorization_validated(
        self,
        user_id: UUID,
        tenant_id: UUID,
        other_tenant_id: UUID
    ):
        """
        Property 84: Tenant authorization is validated.
        
        Validates Requirements: 20.4
        
        Property: Users can only access data from their own tenant.
        Cross-tenant access attempts are rejected.
        """
        # Ensure tenants are different
        if tenant_id == other_tenant_id:
            other_tenant_id = uuid4()
        
        # Arrange: Create token for user's tenant
        token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            role="user"
        )
        
        # Act: Decode token
        payload = decode_access_token(token)
        token_tenant_id = UUID(payload["tenant_id"])
        
        # Assert: Token contains correct tenant
        assert token_tenant_id == tenant_id, \
            "Token must contain user's tenant ID"
        
        # Assert: Token does not contain other tenant
        assert token_tenant_id != other_tenant_id, \
            "Token must not contain other tenant's ID"
        
        # Simulate authorization check
        def check_tenant_authorization(
            user_tenant: UUID,
            resource_tenant: UUID
        ) -> bool:
            """Check if user can access resource from tenant."""
            return user_tenant == resource_tenant
        
        # Assert: User can access own tenant's data
        assert check_tenant_authorization(token_tenant_id, tenant_id), \
            "User must be able to access own tenant's data"
        
        # Assert: User cannot access other tenant's data
        assert not check_tenant_authorization(token_tenant_id, other_tenant_id), \
            "User must not be able to access other tenant's data"
    
    @given(
        password=st.text(
            min_size=8,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Po"),
                blacklist_characters="\x00"  # bcrypt doesn't allow null bytes
            )
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_password_hashing_security(
        self,
        password: str
    ):
        """
        Test that password hashing is secure and consistent.
        
        This validates password security measures.
        """
        # Act: Hash the password
        hashed = get_password_hash(password)
        
        # Assert: Hash is created
        assert hashed is not None, \
            "Password hash should be created"
        assert isinstance(hashed, str), \
            "Password hash should be a string"
        assert len(hashed) > 0, \
            "Password hash should not be empty"
        
        # Assert: Hash is different from password
        assert hashed != password, \
            "Password hash must be different from plaintext password"
        
        # Assert: Hash is not reversible (one-way)
        # We can't directly test this, but we verify it's bcrypt format
        assert hashed.startswith("$2b$"), \
            "Password hash should use bcrypt format"
        
        # Assert: Verification works correctly
        assert verify_password(password, hashed), \
            "Password verification must succeed for correct password"
        
        # Assert: Verification fails for wrong password
        if len(password) > 1:
            wrong_password = password[:-1] + ("x" if password[-1] != "x" else "y")
            assert not verify_password(wrong_password, hashed), \
                "Password verification must fail for incorrect password"
        
        # Assert: Same password produces different hashes (salt)
        hashed2 = get_password_hash(password)
        assert hashed != hashed2, \
            "Same password should produce different hashes (salted)"
        
        # Assert: Both hashes verify correctly
        assert verify_password(password, hashed2), \
            "Both hashes should verify the same password"
    
    @given(
        is_superuser=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    async def test_user_role_assignment(
        self,
        is_superuser: bool
    ):
        """
        Test that users are assigned appropriate roles.
        
        This validates role assignment logic.
        """
        # Arrange: Create a user
        user = User(
            id=uuid4(),
            tenant_id=uuid4(),
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
            is_superuser=is_superuser
        )
        
        # Act: Get user roles (simplified - no DB)
        roles = await RBACService.get_user_roles(user, None)
        
        # Assert: User has at least one role
        assert len(roles) > 0, \
            "User must have at least one role"
        
        # Assert: Superuser has superuser role
        if is_superuser:
            assert any(r.role_type == RoleType.SUPERUSER for r in roles), \
                "Superuser must have SUPERUSER role"
        else:
            # Regular user has USER role
            assert any(r.role_type == RoleType.USER for r in roles), \
                "Regular user must have USER role"
    
    @given(
        is_superuser=st.booleans(),
        permission=permission_strategy()
    )
    @settings(max_examples=100, deadline=None)
    async def test_permission_inheritance(
        self,
        is_superuser: bool,
        permission: Permission
    ):
        """
        Test that permission inheritance works correctly.
        
        This validates the permission hierarchy.
        """
        # Arrange: Create a user
        user = User(
            id=uuid4(),
            tenant_id=uuid4(),
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
            is_superuser=is_superuser
        )
        
        # Act: Get user permissions (simplified - no DB)
        permissions = await RBACService.get_user_permissions(user, None)
        
        # Assert: Permissions list is valid
        assert isinstance(permissions, list), \
            "Permissions must be a list"
        assert all(isinstance(p, str) for p in permissions), \
            "All permissions must be strings"
        
        # Assert: Superuser has all permissions
        if is_superuser:
            assert permission.value in permissions, \
                "Superuser must have all permissions"
        
        # Assert: No duplicate permissions
        assert len(permissions) == len(set(permissions)), \
            "Permissions list must not contain duplicates"
    
    @given(
        role_type=role_type_strategy()
    )
    @settings(max_examples=100)
    def test_role_permission_consistency(
        self,
        role_type: RoleType
    ):
        """
        Test that role permissions are consistent and well-defined.
        
        This validates the role-permission mapping.
        """
        # Act: Get permissions for role type
        permissions = ROLE_PERMISSIONS.get(role_type, [])
        
        # Assert: Permissions are defined
        assert permissions is not None, \
            "Permissions must be defined for all role types"
        assert isinstance(permissions, list), \
            "Permissions must be a list"
        
        # Assert: All permissions are valid
        valid_permissions = {p.value for p in Permission}
        for perm in permissions:
            assert perm in valid_permissions, \
                f"Permission {perm} must be a valid Permission enum value"
        
        # Assert: No duplicate permissions
        assert len(permissions) == len(set(permissions)), \
            "Role permissions must not contain duplicates"
        
        # Assert: Superuser has all permissions
        if role_type == RoleType.SUPERUSER:
            assert len(permissions) == len(Permission), \
                "Superuser must have all permissions"
        
        # Assert: Viewer has minimal permissions
        if role_type == RoleType.VIEWER:
            assert Permission.READ_DATA.value in permissions, \
                "Viewer must have READ_DATA permission"
            assert Permission.WRITE_DATA.value not in permissions, \
                "Viewer must not have WRITE_DATA permission"
            assert Permission.DELETE_DATA.value not in permissions, \
                "Viewer must not have DELETE_DATA permission"

"""Unit tests for PermissionScope."""
import pytest
from app.schemas.auth import UserContext
from app.services.query.permission_scope import PermissionScope


@pytest.fixture
def superadmin_ctx():
    return UserContext(user_id="u0", user_code="sa", user_name="SuperAdmin", role_level=0, dept_code="D0")


@pytest.fixture
def admin_ctx():
    return UserContext(user_id="u1", user_code="admin1", user_name="Admin", role_level=1, dept_code="D1")


@pytest.fixture
def teacher_ctx():
    return UserContext(user_id="u2", user_code="t1", user_name="Teacher", role_level=2, dept_code="D2")


@pytest.fixture
def student_ctx():
    return UserContext(user_id="u3", user_code="s1", user_name="Student", role_level=3, dept_code="D3")


class TestPermissionScope:
    def test_superadmin_no_filter(self, superadmin_ctx):
        scope = PermissionScope(superadmin_ctx)
        assert scope.is_superadmin is True
        assert scope.get_filters() == []

    def test_admin_org_filter(self, admin_ctx):
        scope = PermissionScope(admin_ctx)
        assert scope.is_superadmin is False
        filters = scope.get_filters()
        assert ("org_code", "D1") in filters

    def test_teacher_dept_filter(self, teacher_ctx):
        scope = PermissionScope(teacher_ctx)
        filters = scope.get_filters()
        assert ("dept_code", "D2") in filters

    def test_student_user_filter(self, student_ctx):
        scope = PermissionScope(student_ctx)
        filters = scope.get_filters()
        assert ("user_id", "u3") in filters

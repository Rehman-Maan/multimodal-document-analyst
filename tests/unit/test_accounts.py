import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from apps.workspaces.models import WorkspaceMembership


pytestmark = pytest.mark.django_db


def test_signup_creates_and_logs_in_user(client):
    response = client.post(
        reverse("signup"),
        {
            "username": "new_user",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == "/"
    user = get_user_model().objects.get(username="new_user")
    assert user.check_password("StrongPass123!")
    assert "_auth_user_id" in client.session


def test_seed_demo_users_creates_admin_and_workspace_memberships():
    call_command("seed_demo_users", password="TestPass123!", admin_password="AdminPass123!")

    User = get_user_model()
    admin = User.objects.get(username="admin")
    assert admin.is_staff
    assert admin.is_superuser
    assert admin.check_password("AdminPass123!")

    memberships = WorkspaceMembership.objects.filter(workspace__slug="demo-workspace")
    assert memberships.count() == 5
    assert set(memberships.values_list("role", flat=True)) == {
        WorkspaceMembership.Role.OWNER,
        WorkspaceMembership.Role.ADMIN,
        WorkspaceMembership.Role.REVIEWER,
        WorkspaceMembership.Role.ANALYST,
        WorkspaceMembership.Role.VIEWER,
    }

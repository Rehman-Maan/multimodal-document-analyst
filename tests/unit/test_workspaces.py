import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.workspaces.models import Workspace, WorkspaceMembership


pytestmark = pytest.mark.django_db


def test_workspace_creation_assigns_unique_slug():
    user = get_user_model().objects.create_user(username="owner", password="pass")
    first = Workspace.objects.create(name="Finance Ops", created_by=user)
    second = Workspace.objects.create(name="Finance Ops", created_by=user)

    assert first.slug == "finance-ops"
    assert second.slug == "finance-ops-2"


def test_owner_membership_role_helpers():
    user = get_user_model().objects.create_user(username="owner", password="pass")
    workspace = Workspace.objects.create(name="Review Team", created_by=user)
    membership = WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.OWNER,
    )

    assert membership.can_manage_workspace
    assert membership.can_review_documents
    assert membership.can_analyze_documents
    assert membership.can_view_documents
    assert workspace.user_can_manage(user)


def test_workspace_list_requires_login(client):
    response = client.get(reverse("workspace-list"))

    assert response.status_code == 302
    assert reverse("login") in response["Location"]


def test_workspace_create_view_adds_owner_membership(client):
    user = get_user_model().objects.create_user(username="owner", password="pass")
    client.force_login(user)

    response = client.post(reverse("workspace-create"), {"name": "Claims Desk"})

    workspace = Workspace.objects.get(name="Claims Desk")
    assert response.status_code == 302
    assert workspace.membership_for(user).role == WorkspaceMembership.Role.OWNER


def test_workspace_api_lists_only_current_user_memberships(client):
    user = get_user_model().objects.create_user(username="analyst", password="pass")
    other = get_user_model().objects.create_user(username="other", password="pass")
    visible = Workspace.objects.create(name="Visible", created_by=user)
    hidden = Workspace.objects.create(name="Hidden", created_by=other)
    WorkspaceMembership.objects.create(
        workspace=visible,
        user=user,
        role=WorkspaceMembership.Role.ANALYST,
    )
    WorkspaceMembership.objects.create(
        workspace=hidden,
        user=other,
        role=WorkspaceMembership.Role.OWNER,
    )
    client.force_login(user)

    response = client.get(reverse("api-workspace-list"))

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Visible"]

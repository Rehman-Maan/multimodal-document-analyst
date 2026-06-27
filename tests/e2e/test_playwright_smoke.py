import pytest
from django.contrib.auth import get_user_model
from PIL import Image

from apps.schemas.models import ensure_default_document_types_and_schemas
from apps.workspaces.models import Workspace, WorkspaceMembership


pytestmark = [pytest.mark.django_db, pytest.mark.e2e]


def test_user_can_login_open_dashboard_and_upload_image(live_server, tmp_path, settings):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.OPENAI_API_KEY = ""

    user = get_user_model().objects.create_user(username="e2e_owner", password="TestPass123!")
    workspace = Workspace.objects.create(name="E2E Documents", created_by=user)
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.OWNER,
    )
    ensure_default_document_types_and_schemas(workspace, user)

    upload_file = tmp_path / "receipt-smoke.png"
    Image.new("RGB", (640, 360), color=(245, 248, 246)).save(upload_file)

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception as exc:
            if "Executable doesn't exist" in str(exc):
                pytest.skip("Playwright Chromium is not installed locally.")
            raise
        page = browser.new_page()
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_label("Username").fill("e2e_owner")
        page.get_by_label("Password").fill("TestPass123!")
        page.get_by_role("button", name="Sign in").click()

        page.get_by_role("heading", name="Workspaces").wait_for()
        page.get_by_role("heading", name="E2E Documents").wait_for()
        page.get_by_role("link", name="Open dashboard").click()
        page.get_by_role("heading", name="E2E Documents").wait_for()
        page.get_by_role("link", name="Upload document").first.click()
        page.get_by_label("Title").fill("Smoke Receipt")
        page.get_by_label("Document type").select_option("receipt")
        page.get_by_label("File").set_input_files(str(upload_file))
        page.get_by_role("button", name="Upload document").click()

        page.get_by_role("heading", name="Smoke Receipt").wait_for()
        page.locator(".status-pill", has_text="Processed").wait_for()
        page.get_by_text("Pages and extracted text").wait_for()
        browser.close()

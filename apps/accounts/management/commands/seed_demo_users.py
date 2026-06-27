from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.schemas.models import ensure_default_document_types_and_schemas
from apps.workspaces.models import Workspace, WorkspaceMembership


DEMO_USERS = [
    ("demo_owner", WorkspaceMembership.Role.OWNER),
    ("demo_admin", WorkspaceMembership.Role.ADMIN),
    ("demo_reviewer", WorkspaceMembership.Role.REVIEWER),
    ("demo_analyst", WorkspaceMembership.Role.ANALYST),
    ("demo_viewer", WorkspaceMembership.Role.VIEWER),
]


class Command(BaseCommand):
    help = "Create local demo users, an admin account, and a demo workspace."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="TestPass123!")
        parser.add_argument("--admin-password", default="AdminPass123!")

    def handle(self, *args, **options):
        User = get_user_model()
        password = options["password"]
        admin_password = options["admin_password"]

        admin, created_admin = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(admin_password)
        admin.save(update_fields=["email", "is_staff", "is_superuser", "password"])

        owner = None
        for username, _role in DEMO_USERS:
            user, _created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            user.set_password(password)
            user.save(update_fields=["email", "password"])
            if username == "demo_owner":
                owner = user

        workspace, created_workspace = Workspace.objects.get_or_create(
            slug="demo-workspace",
            defaults={"name": "Demo Workspace", "created_by": owner},
        )
        if created_workspace:
            ensure_default_document_types_and_schemas(workspace, owner)

        for username, role in DEMO_USERS:
            user = User.objects.get(username=username)
            WorkspaceMembership.objects.update_or_create(
                workspace=workspace,
                user=user,
                defaults={"role": role},
            )

        self.stdout.write(self.style.SUCCESS("Demo users ready."))
        self.stdout.write(f"admin / {admin_password}")
        self.stdout.write(f"demo_owner, demo_admin, demo_reviewer, demo_analyst, demo_viewer / {password}")
        if created_admin:
            self.stdout.write("Created admin superuser.")
        if created_workspace:
            self.stdout.write("Created Demo Workspace.")

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Workspace(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_workspaces",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="WorkspaceMembership",
        related_name="workspaces",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = self._build_unique_slug()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("workspace-dashboard", kwargs={"slug": self.slug})

    def membership_for(self, user):
        if not user or not user.is_authenticated:
            return None
        return self.memberships.filter(user=user).first()

    def user_role(self, user) -> str:
        membership = self.membership_for(user)
        return membership.role if membership else ""

    def user_can_view(self, user) -> bool:
        return self.membership_for(user) is not None

    def user_can_manage(self, user) -> bool:
        membership = self.membership_for(user)
        return bool(membership and membership.can_manage_workspace)

    def _build_unique_slug(self) -> str:
        base_slug = slugify(self.name) or "workspace"
        candidate = base_slug
        counter = 2
        while Workspace.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate


class WorkspaceMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        REVIEWER = "reviewer", "Reviewer"
        ANALYST = "analyst", "Analyst"
        VIEWER = "viewer", "Viewer"

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"],
                name="unique_workspace_membership",
            )
        ]
        indexes = [
            models.Index(fields=["workspace", "role"]),
            models.Index(fields=["user", "role"]),
        ]
        ordering = ["workspace__name", "user__username"]

    def __str__(self) -> str:
        return f"{self.user} in {self.workspace} as {self.role}"

    @property
    def can_manage_workspace(self) -> bool:
        return self.role in {self.Role.OWNER, self.Role.ADMIN}

    @property
    def can_review_documents(self) -> bool:
        return self.role in {self.Role.OWNER, self.Role.ADMIN, self.Role.REVIEWER}

    @property
    def can_analyze_documents(self) -> bool:
        return self.role in {
            self.Role.OWNER,
            self.Role.ADMIN,
            self.Role.REVIEWER,
            self.Role.ANALYST,
        }

    @property
    def can_view_documents(self) -> bool:
        return self.role in set(self.Role.values)

from django import forms

from apps.workspaces.models import Workspace


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "autocomplete": "organization",
                    "placeholder": "Operations Team",
                }
            )
        }

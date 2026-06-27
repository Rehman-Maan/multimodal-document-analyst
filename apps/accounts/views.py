from django.contrib import messages
from django.contrib.auth import login
from django.views.generic import CreateView

from apps.accounts.forms import SignUpForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = "/"

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Account created.")
        return response

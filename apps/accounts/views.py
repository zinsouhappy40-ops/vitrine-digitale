from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .forms import EmailAuthenticationForm


def login_email_key(group, request):
    return (request.POST.get("username") or "").strip().casefold()


@method_decorator(
    ratelimit(key=login_email_key, rate="5/10m", method="POST", block=False),
    name="dispatch",
)
@method_decorator(
    ratelimit(key="ip", rate="5/10m", method="POST", block=False),
    name="dispatch",
)
class EmailLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST" and getattr(request, "limited", False):
            form = self.get_form()
            context = self.get_context_data(form=form, rate_limited=True)
            return self.render_to_response(context, status=429)
        return super().dispatch(request, *args, **kwargs)


class AccountLogoutView(LogoutView):
    http_method_names = ["post", "options"]
    next_page = reverse_lazy("accounts:login")

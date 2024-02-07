from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

class ChitfundLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and the owner."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_chitfund_owner or request.user.is_namegen_user:
            return redirect("client:client-list")
        return super().dispatch(request, *args, **kwargs)
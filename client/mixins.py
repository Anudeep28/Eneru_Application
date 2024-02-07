from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

class ClientLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and the owner."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not any([request.user.is_chitfund_user,request.user.is_chitfund_owner]):
            return redirect("client:client-restrict")
        return super().dispatch(request, *args, **kwargs)
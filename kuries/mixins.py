from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

class ChitfundLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and the owner."""

    def dispatch(self, request, *args, **kwargs):
        #print("mixin",request.user.is_authenticated, request.user.is_chitfund_owner)
        if not request.user.is_authenticated or not request.user.is_chitfund_owner:
            return redirect("kuries:chitfund-list")
        return super().dispatch(request, *args, **kwargs)
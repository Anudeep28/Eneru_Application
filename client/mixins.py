from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

class ClientLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and the owner."""

    def dispatch(self, request, *args, **kwargs):
<<<<<<< HEAD
        #print("mixin ",request.user.is_authenticated, request.user.is_chitfund_owner, request.user.is_chitfund_user)
=======
>>>>>>> 85d3363fc61e3361175fae53437af7452a1dd83f
        if not request.user.is_authenticated or not any([request.user.is_chitfund_owner,request.user.is_chitfund_user]):
            return redirect("client:client-restrict")
        return super().dispatch(request, *args, **kwargs)


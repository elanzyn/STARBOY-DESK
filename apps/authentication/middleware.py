from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class RoleRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Exemplo: proteger rotas específicas
        if hasattr(view_func, 'role_required'):
            required_role = getattr(view_func, 'role_required')
            if not request.user.is_authenticated or request.user.cargo != required_role:
                return redirect(reverse('authentication:login'))
        return None

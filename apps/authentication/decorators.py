from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.cargo != role:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def superadmin_required(view_func):
    return role_required('SUPER_ADMIN')(view_func)

def admin_required(view_func):
    return role_required('ADMIN')(view_func)

def user_required(view_func):
    return role_required('USER')(view_func)

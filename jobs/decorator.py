from django.shortcuts import redirect
from django.contrib import messages
def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_staff:
            messages.error(request, "Access denied.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_superuser:
            messages.error(request, "Admin access required.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper

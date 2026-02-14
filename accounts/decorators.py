from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


# ---------------------------------------------------
# ADMIN ONLY (Superuser)
# ---------------------------------------------------
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, "Admin access required.")
        return redirect("dashboard")

    return wrapper


# ---------------------------------------------------
# TRAINER / CONSULTANT ONLY (Staff but NOT superuser)
# ---------------------------------------------------
def trainer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.is_staff and not request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, "Trainer access required.")
        return redirect("dashboard")

    return wrapper


# ---------------------------------------------------
# LEGACY STAFF (temporary compatibility — remove later)
# ---------------------------------------------------
def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.is_staff:
            return view_func(request, *args, **kwargs)

        messages.error(request, "Access denied.")
        return redirect("dashboard")

    return wrapper

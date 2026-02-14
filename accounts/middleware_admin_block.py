from django.shortcuts import redirect

class BlockTrainerAdminMiddleware:
    """
    Prevent trainers (is_staff=True, is_superuser=False)
    from opening Django Admin panel.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith("/admin/"):

            if request.user.is_authenticated:
                if request.user.is_staff and not request.user.is_superuser:
                    return redirect("trainer_dashboard")

        return self.get_response(request)

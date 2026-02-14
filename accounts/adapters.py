from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        extra_data = sociallogin.account.extra_data
        full_name = extra_data.get("name", "").strip()

        if full_name:
            # Save name on User model
            user.full_name = full_name
            user.save(update_fields=["full_name"])

            # Save name on Profile
            if hasattr(user, "profile"):
                user.profile.full_name = full_name
                user.profile.save(update_fields=["full_name"])

        return user


    # ⭐⭐⭐ ADD THIS FUNCTION ⭐⭐⭐
    def get_login_redirect_url(self, request):
        return reverse("public_home")

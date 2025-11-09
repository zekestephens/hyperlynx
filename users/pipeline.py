from django.shortcuts import redirect
from django.urls import reverse

from users.models import Users


def redirect_if_incomplete_profile(backend, user: Users, response, *args, **kwargs):
    """
    Redirect to profile completion if phone_number is null.
    This runs AFTER the user is authenticated.
    """
    if user:
        if user.jira_username is None:
            # Use Django's redirect with reverse to ensure URL is correct
            return redirect('first_login_prompt')

    # If profile is complete, continue normally
    return None
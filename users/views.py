from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import quote_plus, urlencode
from django.conf import settings

def logout_view(request):
    logout(request)

    return redirect(
        f"https://{settings.SOCIAL_AUTH_AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("index")),
                "client_id": settings.SOCIAL_AUTH_AUTH0_KEY,
            },
            quote_via=quote_plus,
        ),
        )
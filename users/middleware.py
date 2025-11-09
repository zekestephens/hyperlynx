from django.shortcuts import redirect

class CompleteProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # URLs that should NOT trigger the redirect
        self.exempt_urls = [
            '/auth/first-login-prompt/',  # The completion page itself
            '/logout/',
            '/auth/',  # All auth0 callback URLs
            '/admin/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Only check authenticated users
        if request.user.is_authenticated:
            # Check if current URL is exempt
            is_exempt = any(request.path.startswith(url) for url in self.exempt_urls)

            if not is_exempt:
                # Check if user needs to complete profile
                if request.user.jira_username is None:  # Change to your field name
                        return redirect('first_login_prompt')

        return self.get_response(request)
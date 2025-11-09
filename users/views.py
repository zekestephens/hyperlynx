from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import quote_plus, urlencode
from django.conf import settings

from .forms import JIRAUsernameForm


def first_login_prompt_view(request):
    if not request.user.requires_jira_username:
        return redirect('index')
    if request.method == 'POST':
        form = JIRAUsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            # Set the flag to indicate completion
            user.requires_xx_username = False
            user.save()
            return redirect('index') # Redirect to the main page
    else:
        form = JIRAUsernameForm(instance=request.user)

    return render(request, 'first_login_prompt.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Users
from .forms import JIRAUsernameForm

@login_required
def first_login(request):
    profile: Users = request.user

    # Check if jira username is null
    if request.user.jira_username is None:
        if request.method == 'POST':
            form = JIRAUsernameForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect('index')  # Redirect to same page or elsewhere
        else:
            form = JIRAUsernameForm(instance=request.user)

        return render(request, 'profile_setup.html', {'form': form})

    # If jira username is set, show regular profile page
    return redirect('index')

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
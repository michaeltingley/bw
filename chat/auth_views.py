"""Views related to authentication and the login process."""

from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import View

from .models import Participant

class LoginView(View):
    """Handles login page operations."""

    def get(self, request):
        """Renders the login page."""
        return render(request, 'chat/login.html')

    def post(self, request):
        """REST endpoint to log in or create a new participant.

        Args:
            POST['email'] (str): The email to log in to or sign up with.
            POST['password'] (str): The password to use with the associated
                email.
            POST['sign_up']: If this field is present, the request will be
                interpreted as a request to sign up. Otherwise, the request will
                be interpreted as a request to log in.

        Returns:
            HttpResponseRedirect. Redirects to the chat page if the request was
            successful.
        """
        email = request.POST['email']
        if not email:
            return login_failed(request, 'Email must not be blank.')

        password = request.POST['password']
        if not email:
            return login_failed(request, 'Password must not be blank.')

        if 'sign_up' in request.POST:
            if User.objects.filter(username=email).exists():
                return login_failed(
                    request,
                    "The provided email already exists. Try logging in."
                )
            created_user = User.objects.create_user(
                username=email,
                password=password
            )
            Participant.objects.create(user=created_user)
        user = auth.authenticate(username=email, password=password)
        if user is None:
            return login_failed(
                request,
                "Your email and password didn't match. Please try again."
            )
        auth.login(request, user)
        return HttpResponseRedirect('/chat/')

def login_failed(request, error):
    """Renders the login page with the specified error."""
    return render(request, 'chat/login.html', {'error': error})

def logout(request):
    """Logs the user out and renders the index."""
    auth.logout(request)
    return HttpResponseRedirect('/chat/')

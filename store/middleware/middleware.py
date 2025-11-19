from django.conf import settings
from django.contrib.auth import logout
# import requests

class AdminSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is an admin URL
        is_admin_url = request.path.startswith('/myadmin/') or request.path == '/admin-login/'
        
        if is_admin_url:
            # Use admin session cookie for admin pages
            request.session_cookie_name = settings.ADMIN_SESSION_COOKIE_NAME
        else:
            # Use regular session cookie for user pages
            request.session_cookie_name = settings.SESSION_COOKIE_NAME
        
        response = self.get_response(request)
        
        # Ensure admin sessions are isolated
        if is_admin_url and hasattr(request, 'user') and request.user.is_authenticated:
            if not (request.user.is_staff or request.user.is_superuser):
                # Log out non-admin users from admin session
                logout(request)
        
        return response

    def process_request(self, request):
        # Set the session cookie key based on the URL
        if request.path.startswith('/myadmin/') or request.path == '/admin-login/':
            request.COOKIES[settings.SESSION_COOKIE_NAME] = request.COOKIES.get(
                settings.ADMIN_SESSION_COOKIE_NAME, ''
            )
        else:
            # For regular pages, don't use admin session
            request.COOKIES[settings.SESSION_COOKIE_NAME] = request.COOKIES.get(
                settings.SESSION_COOKIE_NAME, ''
            )
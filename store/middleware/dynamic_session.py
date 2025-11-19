from django.conf import settings

class DynamicSessionCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Keep original session cookie name
        original_cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')

        # Check if the request is for admin
        if request.path.startswith('/admin'):
            # Use a separate cookie name for admin
            settings.SESSION_COOKIE_NAME = getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')
        else:
            # Keep frontend cookie for user pages
            settings.SESSION_COOKIE_NAME = getattr(settings, 'USER_SESSION_COOKIE_NAME', 'user_sessionid')

        response = self.get_response(request)

        # Restore original session setting so it doesn’t leak to other requests
        settings.SESSION_COOKIE_NAME = original_cookie_name

        return response

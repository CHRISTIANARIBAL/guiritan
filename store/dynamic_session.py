from django.conf import settings

class DynamicSessionCookieMiddleware:
    """
    Dynamically switch session cookie name based on URL.
    Admin pages use 'admin_sessionid', user pages use 'user_sessionid'.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- Detect admin-related URLs ---
        admin_paths = ['/admin_login', '/myadmin', '/admin_logout', '/admin']
        if any(request.path.startswith(p) for p in admin_paths):
            # use admin cookie
            settings.SESSION_COOKIE_NAME = settings.ADMIN_SESSION_COOKIE_NAME
        else:
            # use user cookie
            settings.SESSION_COOKIE_NAME = settings.USER_SESSION_COOKIE_NAME

        response = self.get_response(request)
        return response

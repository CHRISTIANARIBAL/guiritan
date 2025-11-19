# store/middleware/separate_session.py
from django.conf import settings

class SeparateSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Separate session for admin panel
        if path.startswith('/admin') or path.startswith('/myadmin'):
            session_cookie_name = getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')
        else:
            session_cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')

        # Apply the selected session cookie name
        request.session_cookie_name = session_cookie_name

        response = self.get_response(request)

        # Ensure cookie is correctly set in response
        if hasattr(request, 'session') and request.session.modified:
            response.set_cookie(
                request.session_cookie_name,
                request.session.session_key,
                max_age=settings.SESSION_COOKIE_AGE,
                httponly=True,
                secure=settings.SESSION_COOKIE_SECURE,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )

        return response

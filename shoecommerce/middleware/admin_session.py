from django.conf import settings

class AdminSeparateSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for the admin site
        if request.path.startswith('/admin'):
            settings.SESSION_COOKIE_NAME = 'admin_sessionid'
        else:
            settings.SESSION_COOKIE_NAME = 'user_sessionid'
        response = self.get_response(request)
        return response

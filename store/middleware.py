from django.utils.deprecation import MiddlewareMixin

class SeparateSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/admin'):
            request.session.set_test_cookie()  # ensures session is initialized
            request.session_cookie_name = 'admin_sessionid'
        else:
            request.session.set_test_cookie()
            request.session_cookie_name = 'user_sessionid'

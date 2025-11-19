from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.utils.http import http_date

class SeparateAdminSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Just detect admin path — no need to manually save sessions
        if request.path.startswith('/admin'):
            request.is_admin_path = True
        else:
            request.is_admin_path = False

    def process_response(self, request, response):
        # Use a different cookie name for admin
        if getattr(request, 'is_admin_path', False):
            expires = timezone.now() + timezone.timedelta(hours=2)
            response.set_cookie(
                'adminsession',
                '1',
                httponly=True,
                expires=http_date(expires.timestamp())
            )
        return response

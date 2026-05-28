from audit.models import AuditLog
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType


class SecurityAuditMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        return None


def log_access_denied(request, reason):
    user = request.user if request.user.is_authenticated else None

    AuditLog.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        action_type='access_denied',
        description=f"Доступ запрещён: {reason}",
    )


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
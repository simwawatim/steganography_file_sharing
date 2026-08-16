import functools

from django.contrib.auth import get_user_model
from core.models import ActivityLog

User = get_user_model()


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _find_request(args):
    """
    Works whether the decorated function is a DRF method (self, request, ...)
    or a plain function-based view (request, ...) - just grabs whichever
    positional arg looks like an HttpRequest/DRF Request.
    """
    for arg in args:
        if hasattr(arg, "user") and hasattr(arg, "method"):
            return arg
    return None


def log_activity(action, description=None, get_target=None, get_user=None):
    """
    Records an ActivityLog row every time the wrapped view runs.

    action:      short machine-readable code, e.g. "file.upload", "auth.login"
    description: static string, OR a callable(request, response) -> str
                 for something dynamic (e.g. include a filename)
    get_target:  optional callable(request, response) -> model instance,
                 used to set the generic FK "target" on the log row
                 (e.g. the UserFile that was just uploaded)
    get_user:    optional callable(request, response) -> User instance or None.
                 Use this on AllowAny views (signup/login) where request.user
                 is still AnonymousUser when this runs, so the default
                 "request.user if authenticated" lookup can't attribute the
                 attempt to an actual account.

    Logging failures never break the actual request - if anything in the
    logging path raises, it's swallowed so the real response still goes out.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            request = _find_request(args)
            response = None
            status_value = ActivityLog.ActionStatus.SUCCESS
            error_message = None

            try:
                response = view_func(*args, **kwargs)
                if getattr(response, "status_code", 200) >= 400:
                    status_value = ActivityLog.ActionStatus.FAILURE
                return response
            except Exception as exc:
                status_value = ActivityLog.ActionStatus.FAILURE
                error_message = str(exc)
                raise
            finally:
                if request is not None:
                    try:
                        desc = (
                            description(request, response)
                            if callable(description)
                            else description
                        )
                        target = get_target(request, response) if get_target else None

                        if get_user:
                            log_user = get_user(request, response)
                        else:
                            log_user = (
                                request.user
                                if getattr(request.user, "is_authenticated", False)
                                else None
                            )

                        ActivityLog.objects.create(
                            user=log_user,
                            action=action,
                            description=error_message or desc or "",
                            status=status_value,
                            ip_address=get_client_ip(request),
                            target=target,
                        )
                    except Exception:
                        pass

        return wrapper
    return decorator
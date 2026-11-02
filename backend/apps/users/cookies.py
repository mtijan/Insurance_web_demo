from django.conf import settings
from django.middleware.csrf import get_token, rotate_token


def set_auth_cookies(response, access, refresh=None):
    pairs = [("access_token", access, settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"])]
    if refresh:
        pairs.append(("refresh_token", refresh, settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]))
    for name, value, lifetime in pairs:
        response.set_cookie(name, value, max_age=int(lifetime.total_seconds()),
                            secure=settings.AUTH_COOKIE_SECURE, httponly=True,
                            samesite=settings.AUTH_COOKIE_SAMESITE, path="/")
    response["Cache-Control"] = "no-store"
    return response


def rotate_csrf(request):
    rotate_token(request)
    return get_token(request)

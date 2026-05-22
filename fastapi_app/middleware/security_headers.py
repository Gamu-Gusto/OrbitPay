from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' fonts.googleapis.com; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com fonts.gstatic.com; "
            "font-src 'self' fonts.gstatic.com data:; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com"
        )
        return response

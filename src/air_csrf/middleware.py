import secrets
from collections.abc import Callable, Awaitable
from typing import Any

from starlette.datastructures import FormData
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from .config import CSRFConfig


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware using the double-submit cookie pattern."""

    def __init__(
        self,
        app: ASGIApp,
        config: CSRFConfig | None = None,
        error_response: Callable[[str], Response] | None = None,
    ) -> None:
        super().__init__(app)
        self.config = config or CSRFConfig()
        self.error_response = error_response or self._default_error_response

    @staticmethod
    def _default_error_response(message: str) -> Response:
        return Response(
            content=message,
            status_code=403,
            media_type="text/plain",
        )

    def _should_validate(self, request: Request) -> bool:
        if request.method in self.config.exempt_methods:
            return False
        if request.url.path in self.config.exempt_paths:
            return False
        for prefix in self.config.exempt_path_prefixes:
            if request.url.path.startswith(prefix):
                return False
        return True

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(self.config.token_length)

    def _get_cookie_token(self, request: Request) -> str | None:
        return request.cookies.get(self.config.cookie_name)

    def _get_submitted_token(
        self, request: Request, form_data: FormData | None
    ) -> str | None:
        header_token = request.headers.get(self.config.header_name)
        if header_token:
            return header_token
        if form_data:
            token = form_data.get(self.config.form_field)
            if isinstance(token, str):
                return token
        return None

    def _set_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=self.config.cookie_name,
            value=token,
            max_age=self.config.max_age,
            path="/",
            secure=self.config.secure,
            httponly=False,
            samesite=self.config.samesite,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        cookie_token = self._get_cookie_token(request)
        form_data: FormData | None = None

        if self._should_validate(request):
            content_type = request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                form_data = await request.form()
                request.state._cached_form = form_data

            submitted_token = self._get_submitted_token(request, form_data)

            if not cookie_token:
                return self.error_response("CSRF cookie not set")
            if not submitted_token:
                return self.error_response("CSRF token missing")
            if not secrets.compare_digest(cookie_token, submitted_token):
                return self.error_response("CSRF token mismatch")

        response = await call_next(request)

        if not cookie_token:
            new_token = self._generate_token()
            self._set_cookie(response, new_token)

        return response


def csrf_jinja2_context_processor(
    request: Request, cookie_name: str = "XSRF-TOKEN"
) -> dict[str, Any]:
    """Returns CSRF token for use in Jinja2 templates."""
    token = request.cookies.get(cookie_name, "")
    return {"csrf_token": token}


async def get_form(request: Request) -> FormData:
    """Get form data, using cached version if middleware already parsed it.

    Use this instead of `await request.form()` when using CSRFMiddleware,
    because the middleware consumes the request body to validate the token.
    """
    cached = getattr(request.state, "_cached_form", None)
    if cached is not None:
        return cached
    return await request.form()

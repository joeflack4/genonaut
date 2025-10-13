"""Request-scoped context helpers for timeout diagnostics."""

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Optional

from fastapi import Request


@dataclass(slots=True)
class RequestContext:
    """Metadata about the active HTTP request."""

    path: str
    method: str
    endpoint: Optional[str]
    user_id: Optional[str]


_request_context: ContextVar[Optional[RequestContext]] = ContextVar(
    "request_context",
    default=None,
)


def build_request_context(request: Request) -> RequestContext:
    """Build a request context object from the incoming request."""

    endpoint_name: Optional[str] = None
    endpoint = request.scope.get("endpoint")
    if endpoint is not None:
        endpoint_name = getattr(endpoint, "__name__", None)

    user_id: Optional[str] = request.query_params.get("user_id")
    if not user_id:
        user_id = request.headers.get("x-user-id") or request.headers.get("x-userid")

    if not user_id:
        state_user = getattr(request.state, "user", None)
        if state_user is not None:
            user_id = getattr(state_user, "id", None)
            if user_id is None and isinstance(state_user, dict):
                user_id = state_user.get("id")

    return RequestContext(
        path=request.url.path,
        method=request.method,
        endpoint=endpoint_name,
        user_id=user_id,
    )


def set_request_context(context: RequestContext) -> Token:
    """Set the request context for the current task and return the reset token."""

    return _request_context.set(context)


def reset_request_context(token: Token) -> None:
    """Reset the request context back to the previous value."""

    _request_context.reset(token)


def get_request_context() -> Optional[RequestContext]:
    """Return the current request context, if any."""

    return _request_context.get()

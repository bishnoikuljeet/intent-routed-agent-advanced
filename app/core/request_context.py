import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable for request ID
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())


def set_request_id(request_id: str):
    """Set the request ID for the current context"""
    _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    """Get the request ID for the current context"""
    return _request_id.get()


def get_or_create_request_id() -> str:
    """Get existing request ID or create a new one"""
    request_id = get_request_id()
    if request_id is None:
        request_id = generate_request_id()
        set_request_id(request_id)
    return request_id

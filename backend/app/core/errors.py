"""Standardized error responses and exceptions for Shikhor AI.

Enforces consistent public error schema:
{
  "error": {
    "code": "STABLE_MACHINE_CODE",
    "message": "Safe user-facing message",
    "fieldErrors": {},
    "requestId": "correlation-id"
  }
}
Never leaks raw internal exceptions, database queries, or stack traces.
"""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Stable uppercase machine code")
    message: str = Field(..., description="Safe human-readable user facing message")
    fieldErrors: Dict[str, Any] = Field(default_factory=dict, description="Field-specific validation errors")
    requestId: Optional[str] = Field(None, description="Request correlation identifier")


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class ShikhorException(Exception):
    """Base application exception with machine code and safe message."""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        field_errors: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field_errors = field_errors or {}
        super().__init__(message)


class NotFoundException(ShikhorException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedException(ShikhorException):
    def __init__(self, message: str = "Authentication required", code: str = "UNAUTHORIZED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(ShikhorException):
    def __init__(self, message: str = "Access denied", code: str = "FORBIDDEN"):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN)


class ValidationException(ShikhorException):
    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_ERROR", field_errors: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, field_errors=field_errors)


class ConflictException(ShikhorException):
    def __init__(self, message: str = "Resource conflict", code: str = "CONFLICT"):
        super().__init__(code=code, message=message, status_code=status.HTTP_409_CONFLICT)




def create_error_response(
    code: str,
    message: str,
    status_code: int,
    request_id: Optional[str] = None,
    field_errors: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            fieldErrors=field_errors or {},
            requestId=request_id,
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())

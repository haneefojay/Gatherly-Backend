"""Admin access logging middleware"""

from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.auth import TokenGenerator
from app.core.settings import get_settings
from app.users.models import UserRole

settings = get_settings()

access_token_verifier = TokenGenerator(
    secret_key=settings.SECRET_KEY,
    expire_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
)


class AdminAccessLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all admin API access attempts"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log admin access to audit trail"""
        
        # Only log admin routes
        if not request.url.path.startswith("/admin"):
            return await call_next(request)
        
        admin_id = None
        status_code = None
        
        # Extract admin ID from token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                user_id_str = await access_token_verifier.verify(token, "user")
                if user_id_str:
                    import uuid
                    admin_id = uuid.UUID(user_id_str)
            except Exception:
                pass
        
        # Process request
        response = await call_next(request)
        status_code = response.status_code
        
        # Log to audit trail if admin is authenticated
        if admin_id:
            try:
                from app.common.dependencies import get_session_context
                from app.admin.services import log_admin_action
                
                async with get_session_context() as session:
                    await log_admin_action(
                        session=session,
                        admin_id=admin_id,
                        action="api_access",
                        resource_type="endpoint",
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=status_code,
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                    )
            except Exception as e:
                # Don't let logging errors break the request
                print(f"Failed to log admin access: {e}")
        
        return response

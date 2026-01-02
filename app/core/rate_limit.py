import jwt
from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter

from app.core.settings import get_settings

settings = get_settings()


async def role_based_rate_limiter(request: Request, response: Response):
    """
    Dynamic rate limiter based on user role.
    
    Limits:
    - Admin: 500 req/hour
    - Organizer: 200 req/hour
    - User: 100 req/hour
    - Guest: 30 req/hour
    """
    if settings.TESTING:
        return

    times = settings.REQ_RATE
    seconds = settings.REQ_RATE_TIME
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]

            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"],
                options={"verify_exp": True} 
            )
            role = payload.get("role")
            
            if role == "admin":
                times = settings.REQ_RATE_ADMIN
            elif role == "organizer":
                times = settings.REQ_RATE_ORGANIZER
            elif role == "user":
                times = settings.REQ_RATE_USER
                
        except Exception:
            pass
    
    limiter = RateLimiter(times=times, seconds=seconds)
    await limiter(request, response)

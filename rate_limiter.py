from fastapi import HTTPException, Request, Depends
from typing import Dict, Optional
import time
from collections import defaultdict, deque
import threading
from functools import wraps
import inspect

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if a request is allowed based on rate limiting rules
        
        Args:
            identifier: Unique identifier (IP address, user ID, etc.)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()
        
        with self.lock:
            # Clean old requests outside the time window
            request_times = self.requests[identifier]
            while request_times and request_times[0] <= current_time - window_seconds:
                request_times.popleft()
            
            # Check if we're within the limit
            if len(request_times) >= max_requests:
                return False
            
            # Add current request
            request_times.append(current_time)
            return True
    
    def get_reset_time(self, identifier: str, window_seconds: int) -> Optional[float]:
        """Get the time when the rate limit will reset for this identifier"""
        with self.lock:
            request_times = self.requests[identifier]
            if not request_times:
                return None
            return request_times[0] + window_seconds

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_requests: int = 10, window_seconds: int = 3600, per: str = "ip"):
    """
    Rate limiting decorator for FastAPI endpoints
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds (default: 1 hour)
        per: Rate limit per "ip" or "user" (default: "ip")
    """
    def decorator(func):
        @wraps(func)  # This is important for preserving function metadata
        async def wrapper(*args, **kwargs):
            # Get request object and current_user from the function signature
            request = None
            current_user = None
            
            # Get function signature to properly identify parameters
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Look for request and current_user in the bound arguments
            for param_name, param_value in bound_args.arguments.items():
                if param_name == 'request' or (hasattr(param_value, 'client') and hasattr(param_value, 'headers')):
                    request = param_value
                elif param_name == 'current_user' or (hasattr(param_value, 'id') and hasattr(param_value, 'email')):
                    current_user = param_value
            
            # Determine identifier based on 'per' parameter
            if per == "user" and current_user:
                identifier = f"user_{current_user.id}"
            elif request:
                # Use IP address
                client_ip = request.client.host if request.client else "unknown"
                # Handle potential proxy headers
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    client_ip = forwarded_for.split(",")[0].strip()
                identifier = f"ip_{client_ip}"
            else:
                identifier = "unknown"
            
            # Check rate limit
            if not rate_limiter.is_allowed(identifier, max_requests, window_seconds):
                reset_time = rate_limiter.get_reset_time(identifier, window_seconds)
                retry_after = int(reset_time - time.time()) if reset_time else window_seconds
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Alternative approach using FastAPI dependency injection
def create_rate_limit_dependency(max_requests: int = 10, window_seconds: int = 3600, per: str = "ip"):
    """
    Create a FastAPI dependency for rate limiting
    This is a cleaner approach that works better with FastAPI
    """
    def rate_limit_dependency(request: Request, current_user=None):
        # Determine identifier based on 'per' parameter
        if per == "user" and current_user:
            identifier = f"user_{current_user.id}"
        else:
            # Use IP address
            client_ip = request.client.host if request.client else "unknown"
            # Handle potential proxy headers
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            identifier = f"ip_{client_ip}"
        
        # Check rate limit
        if not rate_limiter.is_allowed(identifier, max_requests, window_seconds):
            reset_time = rate_limiter.get_reset_time(identifier, window_seconds)
            retry_after = int(reset_time - time.time()) if reset_time else window_seconds
            
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        return True
    
    return rate_limit_dependency
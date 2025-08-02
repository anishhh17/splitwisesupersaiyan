from fastapi import HTTPException, Request
from typing import Dict, Optional
import time
from collections import defaultdict, deque
import threading

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
        async def wrapper(*args, **kwargs):
            # Get request object from kwargs
            request = None
            current_user = None
            
            for key, value in kwargs.items():
                if hasattr(value, 'client') and hasattr(value, 'headers'):
                    request = value
                elif hasattr(value, 'id') and hasattr(value, 'email'):
                    current_user = value
            
            # Determine identifier based on 'per' parameter
            if per == "user" and current_user:
                identifier = f"user_{current_user.id}"
            elif request:
                # Use IP address
                client_ip = request.client.host
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
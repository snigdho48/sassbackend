import time
from django.utils.deprecation import MiddlewareMixin
from .models import APIUsage

class APIUsageMiddleware(MiddlewareMixin):
    """Middleware to track API usage for analytics."""
    
    def process_request(self, request):
        # Store start time
        request.start_time = time.time()
    
    def process_response(self, request, response):
        # Only track API requests
        if request.path.startswith('/api/'):
            # Calculate response time
            if hasattr(request, 'start_time'):
                response_time = (time.time() - request.start_time) * 1000  # Convert to milliseconds
                
                # Get user if authenticated
                user = getattr(request, 'user', None)
                if user and user.is_authenticated:
                    # Create API usage record
                    APIUsage.objects.create(
                        user=user,
                        endpoint=request.path,
                        method=request.method,
                        response_time=response_time,
                        status_code=response.status_code
                    )
        
        return response 
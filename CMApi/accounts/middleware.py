# accounts/middleware.py
from django.utils import timezone
from accounts.models import ApiKey
import hashlib
import re
def is_sha256_hash(value):
    """Check if a string looks like a SHA-256 hash."""
    return bool(re.fullmatch(r"[a-f0-9]{64}", value))


class DeveloperFromApiKeyMiddleware:
    """
    Reads X-API-Key or 'Authorization: ApiKey <key>',
    verifies expiry, and attaches request.workspace + request.api_key.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        header_key = (
            request.META.get("api_key", "")
            or request.META.get("HTTP_X_API_KEY", "")
            or request.GET.get("api_key", "")
        )
        
        if not header_key:
            auth = request.META.get("HTTP_AUTHORIZATION", "")
            if auth.lower().startswith("apikey "):
                header_key = auth.split(" ", 1)[1].strip()

        if header_key:
            if is_sha256_hash(header_key):
                hashed_input = header_key
            else:
                hashed_input = hashlib.sha256(header_key.encode()).hexdigest()

            try:
                api_key = ApiKey.objects.get(HashedKey=hashed_input)
                request.developer = api_key.developer
                print(f"Developer attached to request: {request.developer}")
            except ApiKey.DoesNotExist:
                request.developer = None


        return self.get_response(request)

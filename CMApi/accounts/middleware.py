# accounts/middleware.py
from django.utils import timezone
from accounts.models import ApiKey

class WorkspaceFromApiKeyMiddleware:
    """
    Reads X-API-Key or 'Authorization: ApiKey <key>',
    verifies expiry, and attaches request.workspace + request.api_key.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        #print("Request GET parameters:", request.GET)
        #print("Request META:", request.META)
        header_key = request.META.get("api_key", "") or request.META.get("HTTP_X_API_KEY", "") or request.GET.get("api_key","")
        if not key:
            print("no key found")
            auth = request.META.get("HTTP_AUTHORIZATION", "")
            if auth.lower().startswith("apikey "):
                key = auth.split(" ", 1)[1].strip()

        if key:
            try:
                api_key = ApiKey.objects.get(key=header_key, expires_at__gt=now)
                if api_key.expires_at and api_key.expires_at <= timezone.now():
                    print("expiredKey")
                    # expired → don’t attach workspace
                    pass
                else:
                    request.developer = api_key.developer
                    
            except ApiKey.DoesNotExist:
                pass

        return self.get_response(request)

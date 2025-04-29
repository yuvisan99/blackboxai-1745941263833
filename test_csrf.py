from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def csrf_test_view(request):
    return JsonResponse({'message': 'CSRF cookie set'})

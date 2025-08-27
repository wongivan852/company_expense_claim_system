"""URL patterns for reports app."""
from django.urls import path
from django.http import HttpResponse

def placeholder_view(request):
    return HttpResponse("<h2>Reports - Coming Soon</h2>")

app_name = 'reports'
urlpatterns = [path('', placeholder_view, name='index')]
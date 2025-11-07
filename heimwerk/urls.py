"""
heimwerk URL Configuration

This module defines URL routing for the Heimwerk project.

For more information, see:
https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Admin site
    path("admin/", admin.site.urls),
    # Application routes
    path("catalog/", include("serviceCatalog.urls")),
    # Redirect base URL to catalog
    path("", RedirectView.as_view(url="catalog/", permanent=True)),
    # Authentication routes (login, logout, password management)
    path("accounts/", include("django.contrib.auth.urls")),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

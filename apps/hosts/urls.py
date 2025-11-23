# apps/hosts/urls.py
from django.urls import path
from . import views


urlpatterns = [
    path("", views.HostView.as_view(), name="host-form"),
]

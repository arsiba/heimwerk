from django.urls import path

from . import views

urlpatterns = [
    path("deploy/<slug:slug>", views.DeployView.as_view(), name="deploy-instance"),
]

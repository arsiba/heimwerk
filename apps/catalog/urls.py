from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("module/new", views.ModuleCreateView.as_view(), name="module-create"),
    path(
        "module/update/<slug:slug>",
        views.ModuleUpdateView.as_view(),
        name="module-update",
    ),
    path("module/<slug:slug>", views.ModuleDetailView.as_view(), name="module-detail"),
]

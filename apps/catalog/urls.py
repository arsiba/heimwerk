from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("module", views.ModuleListView.as_view(), name="module-list"),
    path("module/<slug:slug>", views.ModuleDetailView.as_view(), name="module-detail"),
    path("deployment", views.InstanceListView.as_view(), name="instance-list"),
    path(
        "instance/<slug:slug>",
        views.InstanceDetailView.as_view(),
        name="instance-detail",
    ),
    path(
        "instance/<uuid:instance_id>/action/",
        views.instance_action_view,
        name="instance-action",
    ),
]

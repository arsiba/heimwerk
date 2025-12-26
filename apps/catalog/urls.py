from django.urls import path, re_path

from . import views, consumers

urlpatterns = [
    path("", views.index, name="index"),
    path("module/new", views.ModuleCreateView.as_view(), name="module-create"),
    path(
        "module/update/<slug:slug>",
        views.ModuleUpdateView.as_view(),
        name="module-update",
    ),
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
websocket_urlpatterns = [
    re_path(r"ws/logs/(?P<pk>[^/]+)/$", consumers.DockerLogConsumer.as_asgi()),
]

from django.urls import path, re_path

from . import views, consumers

urlpatterns = [
    path("deploy/<slug:slug>", views.DeployView.as_view(), name="deploy-instance"),
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
    re_path(r"ws/status/(?P<pk>[^/]+)/$", consumers.InstanceStatusConsumer.as_asgi()),
]

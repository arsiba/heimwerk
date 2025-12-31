from django.urls import path
from apps.users import views

urlpatterns = [path("", views.UsersListView.as_view(), name="user-list")]

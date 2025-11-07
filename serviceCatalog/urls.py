from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('module', views.ModuleListView.as_view(), name='module-list'),
    path('module/<slug:slug>', views.ModuleDetailView.as_view(), name='module-detail')
]
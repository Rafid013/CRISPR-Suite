from django.urls import path, re_path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('new/', views.ProjectCreate.as_view(), name='new'),
    re_path(r'^(?P<pk>[0-9]+)/$', views.ShowProjectView.as_view(), name='show')
]

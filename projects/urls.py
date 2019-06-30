from django.urls import path, re_path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='index'),
    path('create_project/', views.ProjectCreate.as_view(), name='create_project'),
    re_path(r'^(?P<project_id>[0-9]+)/$', views.ShowProjectView.as_view(), name='show_project'),
    re_path(r'^(?P<project_id>[0-9]+)/create_model/$', views.PredictionModelCreate.as_view(), name='create_model'),
    re_path(r'^(?P<project_id>[0-9]+)/(?P<model_id>[0-9]+)/$', views.ShowPredictionModelView.as_view(),
            name='show_model')
]

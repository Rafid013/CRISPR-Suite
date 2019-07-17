from django.urls import path, re_path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='show_project_list'),
    path('api/', views.ProjectListAPIView.as_view(), name='api_show_project_list'),

    path('create_project/', views.ProjectCreateView.as_view(), name='create_project'),
    path('api/create_project/', views.ProjectCreateAPIView.as_view(), name='api_create_project'),

    path('instructions/', views.InstructionView.as_view(), name='instructions'),

    re_path(r'^(?P<project_id>[0-9]+)/$', views.ShowProjectView.as_view(), name='show_project'),
    re_path(r'^api/(?P<project_id>[0-9]+)/$', views.ShowProjectAPIView.as_view(), name='api_show_project'),

    re_path(r'^(?P<project_id>[0-9]+)/create_model/$', views.PredictionModelCreateView.as_view(), name='create_model'),
    re_path(r'^api/(?P<project_id>[0-9]+)/create_model/$', views.PredictionModelCreateAPIView.as_view(),
            name='api_create_model'),

    re_path(r'^(?P<project_id>[0-9]+)/(?P<model_id>[a-z0-9]+)/predict/$', views.PredictView.as_view(),
            name='predict_model'),
    re_path(r'^api/(?P<project_id>[0-9]+)/(?P<model_id>[a-z0-9]+)/predict/$', views.PredictAPIView.as_view(),
            name='api_predict_model'),

    re_path(r'^(?P<project_id>[0-9]+)/(?P<model_id>[a-z0-9]+)/download/$', views.DownloadView.as_view(),
            name='download_prediction'),
    re_path(r'^api/(?P<project_id>[0-9]+)/(?P<model_id>[a-z0-9]+)/download/$', views.DownloadAPIView.as_view(),
            name='api_download_prediction'),

    re_path(r'^(?P<project_id>[0-9]+)/(?P<model_id>[a-z0-9]+)/results/$', views.ResultView.as_view(),
            name='results'),
    re_path(r'^api/(?P<project_id>[0-9]+)/(?P<model_id>[a-z0-9]+)/results/$', views.ResultAPIView.as_view(),
            name='api_results')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

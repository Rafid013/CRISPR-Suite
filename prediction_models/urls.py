from django.urls import path, re_path
from prediction_models import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'prediction_models'

urlpatterns = [
    path('instructions/', views.InstructionView.as_view(), name='instructions'),

    path('', views.PredictionModelListView.as_view(), name='models_list'),
    path('api/', views.PredictionModelListAPIView.as_view(), name='api_models_list'),

    path('create_model/', views.PredictionModelCreateView.as_view(), name='create_model'),
    path('api/create_model/', views.PredictionModelCreateAPIView.as_view(),
         name='api_create_model'),

    re_path(r'^(?P<model_id>[a-z0-9]+)/predict/$', views.PredictView.as_view(),
            name='predict_model'),
    re_path(r'^api/(?P<model_id>[a-z0-9]+)/predict/$', views.PredictAPIView.as_view(),
            name='api_predict_model'),

    re_path(r'^(?P<model_id>[a-z0-9]+)/download/$', views.DownloadView.as_view(),
            name='download_prediction'),
    re_path(r'^api/(?P<model_id>[a-z0-9]+)/download/$', views.DownloadAPIView.as_view(),
            name='api_download_prediction'),

    re_path(r'^(?P<model_id>[a-z0-9]+)/results/$', views.ResultView.as_view(),
            name='results'),
    re_path(r'^api/(?P<model_id>[a-z0-9]+)/results/$', views.ResultAPIView.as_view(),
            name='api_results')
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

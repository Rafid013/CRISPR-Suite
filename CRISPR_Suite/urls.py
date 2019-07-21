from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('prediction_models/', include('prediction_models.urls')),
    path('user/', include('user.urls')),
    path("", views.HomePage.as_view(), name="home"),
    path('about/', views.AboutPage.as_view(), name="about"),
]

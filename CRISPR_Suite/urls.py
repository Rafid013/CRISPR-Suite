from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('prediction_models/', include('prediction_models.urls')),
    path('user/', include('user.urls')),
    path("", views.HomePage.as_view(), name="home"),
    path('about/', views.AboutPage.as_view(), name="about"),
    path('crisprpred/', views.CRISPRpredPage.as_view(), name="crisprpred"),
    path('crisprpred_pp/', views.CRISPRpredPPPage.as_view(), name="crisprpred_pp"),
    path('crisprpred_seq/', views.CRISPRpredSEQPage.as_view(), name="crisprpred_seq"),
    path('publications/', views.PublicationsPage.as_view(), name="publications"),
]

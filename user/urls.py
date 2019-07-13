from django.urls import path
from django.conf.urls import url
from . import views

app_name = 'user'

urlpatterns = [
    path('signup/', views.UserSignUpView.as_view(), name='signup'),
    path('api/signup/', views.UserSignUpRestView.as_view(), name='api_signup'),
    path('login/', views.UserLogInView.as_view(), name='login'),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path('activate/<uid>/<token>', views.activate, name="activate"),
    url(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),
]

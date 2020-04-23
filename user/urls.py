from django.urls import path
from django.conf.urls import url
from . import views
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'user'

urlpatterns = [
    path('signup/', views.UserSignUpView.as_view(), name='signup'),
    path('api/signup/', views.UserSignUpAPIView.as_view(), name='api_signup'),

    path('login/', views.UserLogInView.as_view(), name='login'),
    path('api/login/', obtain_auth_token, name='api_login'),

    path("logout/", views.LogOutView.as_view(), name="logout"),
    path('api/logout/', views.LogOutAPIView.as_view(), name='api_logout'),

    path('activate/<uid>/<token>', views.activate, name="activate"),
    url(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),

    path("password-reset/", views.PasswordResetView.as_view(), name="password-reset"),
    # path('api/password-reset/', views.PasswordResetAPIView.as_view(), name='api_password-reset'),
    path(
        "password-reset-done/",
        views.PasswordResetDoneView.as_view(),
        name="password-reset-done",
    ),
    path(
        "password-reset/<uid>/<token>",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm"
    ),

]

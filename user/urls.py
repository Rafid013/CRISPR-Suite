from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('signup/', views.UserSignUpView.as_view(), name='signup'),
    path('login/', views.UserLogInView.as_view(), name='login')
]

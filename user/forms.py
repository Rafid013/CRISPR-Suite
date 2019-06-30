from django.contrib.auth.models import User
from django import forms


class UserSignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.CharField(widget=forms.EmailInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class UserLogInForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

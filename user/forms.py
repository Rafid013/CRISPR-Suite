from django.contrib.auth.models import User
from django import forms


class UserSignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    email = forms.CharField(widget=forms.EmailInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']


class UserLogInForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class PasswordResetForm(forms.Form):
    email = forms.CharField(widget=forms.EmailInput)


class SetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_new_password = forms.CharField(widget=forms.PasswordInput)